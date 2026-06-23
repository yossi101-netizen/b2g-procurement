"""Multi-source transcript fetcher.

Fallback chain:
  1. youtube-transcript-api — preferred languages
  2. youtube-transcript-api — any language (auto-translated to EN when possible)
  3. yt-dlp — write auto-generated VTT subtitles (different network code path,
     helps when transcript-api is rate-limited but yt-dlp is not)
  4. Whisper API (openai) — opt-in; downloads audio via yt-dlp, transcribes.
     Costs ~$0.006/audio-min. Enable in config: transcript.use_whisper_fallback.

Returns plain UTF-8 text or None if every source fails.
"""
from __future__ import annotations

import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Optional

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

log = logging.getLogger(__name__)


def fetch_transcript(
    video_id: str,
    languages: list[str] | None = None,
    use_whisper_fallback: bool = False,
) -> Optional[str]:
    languages = languages or ["en", "en-US", "en-GB"]

    text = _via_api_preferred(video_id, languages)
    if text:
        return text

    text = _via_api_any(video_id)
    if text:
        return text

    text = _via_ytdlp_subs(video_id, languages)
    if text:
        return text

    if use_whisper_fallback:
        text = _via_whisper(video_id)
        if text:
            return text

    log.warning("No transcript available for %s", video_id)
    return None


def _via_api_preferred(video_id: str, languages: list[str]) -> Optional[str]:
    try:
        chunks = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        return _join(chunks)
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable):
        return None
    except Exception as exc:
        log.debug("transcript-api preferred failed: %s", exc)
        return None


def _via_api_any(video_id: str) -> Optional[str]:
    try:
        listed = YouTubeTranscriptApi.list_transcripts(video_id)
        for t in listed:
            try:
                if t.is_translatable:
                    return _join(t.translate("en").fetch())
                return _join(t.fetch())
            except Exception:
                continue
    except Exception as exc:
        log.debug("transcript-api any-lang failed: %s", exc)
    return None


def _via_ytdlp_subs(video_id: str, languages: list[str]) -> Optional[str]:
    with tempfile.TemporaryDirectory() as tmp:
        opts = {
            "skip_download": True,
            "writeautomaticsub": True,
            "writesubtitles": True,
            "subtitleslangs": languages,
            "subtitlesformat": "vtt",
            "outtmpl": os.path.join(tmp, "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "sleep_requests": 0.5,
            "retries": 3,
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
        except Exception as exc:
            log.debug("yt-dlp subtitle fetch failed: %s", exc)
            return None

        for vtt in Path(tmp).glob(f"{video_id}*.vtt"):
            try:
                return _vtt_to_text(vtt.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue
    return None


def _via_whisper(video_id: str) -> Optional[str]:
    try:
        from openai import OpenAI  # type: ignore
    except ImportError:
        log.warning("Whisper fallback requested but 'openai' package not installed")
        return None

    openai_client = OpenAI()
    with tempfile.TemporaryDirectory() as tmp:
        opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(tmp, "%(id)s.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "64",
            }],
            "quiet": True,
            "no_warnings": True,
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
        except Exception as exc:
            log.error("Audio download for Whisper failed: %s", exc)
            return None

        for audio in Path(tmp).glob(f"{video_id}*.mp3"):
            try:
                with open(audio, "rb") as f:
                    result = openai_client.audio.transcriptions.create(
                        model="whisper-1", file=f
                    )
                return result.text
            except Exception as exc:
                log.error("Whisper transcription failed: %s", exc)
                return None
    return None


def _join(chunks: list[dict]) -> str:
    return " ".join(
        c.get("text", "").strip() for c in chunks if c.get("text")
    )


def _vtt_to_text(vtt: str) -> str:
    """Strip VTT timing/metadata lines; de-duplicate consecutive identical lines."""
    out: list[str] = []
    last = ""
    for raw in vtt.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            continue
        if "-->" in line:
            continue
        # Skip pure timestamp lines
        if re.match(r"^[\d:.,\s]+$", line):
            continue
        cleaned = re.sub(r"<[^>]+>", "", line).strip()
        if cleaned and cleaned != last:
            out.append(cleaned)
            last = cleaned
    return " ".join(out)
