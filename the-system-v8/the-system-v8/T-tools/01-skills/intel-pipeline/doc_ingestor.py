"""
doc_ingestor.py — KritiKaal Intel Pipeline: Phase 1 Document Ingestor

Parses static documents (PDF, TXT, MD) and optionally live web URLs, chunks
them into digestible intel items, and inserts them into intel.db with status
'pending' for LLM filtering and HITL review.

PHASE 1 USE:
  Bulk-load foundational B2B knowledge before enabling automated RSS/Reddit
  polling. Target sources: EUDR regulation text, UK GOV DCTS guidance, ITC
  trade reports, LWG audit standards, tariff schedule PDFs.

INSTALL (PDF support — required for PDF ingestion):
    pip install pdfplumber

INSTALL (URL ingestion — optional):
    pip install requests beautifulsoup4 lxml

USAGE:
    cd T-tools/01-skills/intel-pipeline/

    # Ingest a single file
    python doc_ingestor.py --file docs/eudr-regulation.pdf
    python doc_ingestor.py --file docs/eudr.pdf --title "EUDR Regulation 2023/1115"

    # Trusted source: skip LLM filter, mark as llm_approved directly
    python doc_ingestor.py --file docs/eudr.pdf --trusted

    # Preview chunks without writing to DB
    python doc_ingestor.py --file docs/eudr.pdf --dry-run

    # Ingest all supported files in a directory
    python doc_ingestor.py --dir docs/phase1-sources/

    # Fetch and ingest a live web page (requires requests + beautifulsoup4)
    python doc_ingestor.py --url "https://www.gov.uk/guidance/dcts"

    # Show ingested documents and chunk/status counts
    python doc_ingestor.py --list-docs

    # Show full DB stats
    python doc_ingestor.py --stats

CIRCUIT BREAKER:
  --dir mode halts after MAX_ITEMS_PER_RUN insertions (default: 200).
  Any single document producing > MAX_CHUNKS_PER_DOC chunks triggers a warning.
  Both limits are configurable via constants below.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Shared pipeline core
# ---------------------------------------------------------------------------
_HERE = Path(__file__).parent.resolve()
sys.path.insert(0, str(_HERE))

from intel_core import (
    assign_clusters,
    db_stats,
    get_db,
    has_any_keyword,
    init_db,
    insert_item,
    is_seen,
    make_item_id,
    pre_score,
    update_item_status,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — adjust here, no code changes required
# ---------------------------------------------------------------------------
MAX_CHUNK_CHARS    = 1800   # Characters stored per chunk in the body field
MIN_CHUNK_CHARS    = 120    # Chunks smaller than this are discarded (noise/headers)
MAX_ITEMS_PER_RUN  = 200    # Circuit breaker: --dir halts after this many insertions
MAX_CHUNKS_PER_DOC = 80     # Warn if one document produces more chunks than this

SOURCE_TYPE            = "document"
SUPPORTED_EXTENSIONS   = {".pdf", ".txt", ".md", ".markdown"}


# ---------------------------------------------------------------------------
# PDF text extraction — pdfplumber → pypdf → clear error
# ---------------------------------------------------------------------------

def _extract_pdf_pdfplumber(path: Path) -> str:
    import pdfplumber
    pages = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n\n".join(pages)


def _extract_pdf_pypdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader  # older fallback name
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n\n".join(pages)


def extract_pdf_text(path: Path) -> str:
    """
    Extract text from a PDF. Tries pdfplumber first, then pypdf/PyPDF2.
    Raises ImportError with install instructions if neither is found.
    """
    for extractor, lib_name in [
        (_extract_pdf_pdfplumber, "pdfplumber"),
        (_extract_pdf_pypdf,      "pypdf / PyPDF2"),
    ]:
        try:
            text = extractor(path)
            if text.strip():
                log.debug("  PDF extracted via %s (%d chars)", lib_name, len(text))
                return text
        except ImportError:
            continue
        except Exception as exc:
            log.warning("  PDF extraction error with %s: %s", lib_name, exc)
            continue

    raise ImportError(
        "No PDF parser found. Install one:\n"
        "    pip install pdfplumber\n"
        "  or:\n"
        "    pip install pypdf"
    )


# ---------------------------------------------------------------------------
# URL text extraction — requests + BeautifulSoup
# ---------------------------------------------------------------------------

def extract_url_text(url: str) -> tuple[str, str]:
    """
    Fetch a web page and extract (title, body_text).
    Removes navigation, scripts, footers. Prefers <main> and <article> tags.
    Requires: pip install requests beautifulsoup4 lxml
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        raise ImportError(
            "URL ingestion requires:\n"
            "    pip install requests beautifulsoup4 lxml"
        )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/132.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }

    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")

    # Title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # Strip noise
    for tag in soup(["script", "style", "nav", "footer", "header",
                     "aside", "form", "noscript", "iframe", "button"]):
        tag.decompose()

    # Prefer main content areas
    content = soup.find("main") or soup.find("article") or soup.find("body")
    text = content.get_text(separator="\n") if content else soup.get_text(separator="\n")

    return title, _clean_text(text)


# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------

_MULTI_BLANK   = re.compile(r"\n{3,}")
_MULTI_SPACE   = re.compile(r"[ \t]{2,}")
_PAGE_ARTIFACT = re.compile(
    r"^\s*(Page\s+\d+\s*(of\s*\d+)?|─{3,}|={3,}|-{3,}|\.{5,})\s*$",
    re.MULTILINE | re.IGNORECASE,
)


def _clean_text(text: str) -> str:
    """
    Normalise whitespace and remove PDF artefacts.
    Preserves markdown heading syntax — section titles are used for chunking.
    """
    if not text:
        return ""
    text = _PAGE_ARTIFACT.sub("\n", text)
    text = _MULTI_SPACE.sub(" ", text)
    text = _MULTI_BLANK.sub("\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def _split_markdown_sections(text: str) -> list[tuple[str, str]]:
    """
    Split markdown at heading boundaries (# / ## / ###).
    Returns list of (section_title, section_body) tuples.
    Fallback: returns [(empty_title, full_text)] if no headings found.
    """
    sections: list[tuple[str, str]] = []
    current_title = ""
    current_lines: list[str] = []

    for line in text.splitlines():
        m = re.match(r"^(#{1,3})\s+(.+)", line)
        if m:
            if current_lines:
                body = "\n".join(current_lines).strip()
                if body:
                    sections.append((current_title, body))
            current_title = m.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        body = "\n".join(current_lines).strip()
        if body:
            sections.append((current_title, body))

    return sections if sections else [("", text)]


def _split_at_sentences(text: str, max_chars: int) -> list[str]:
    """Split oversize text at sentence boundaries (. ! ?)."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sent in sentences:
        if current_len + len(sent) + 1 > max_chars and current:
            chunks.append(" ".join(current))
            current = []
            current_len = 0
        current.append(sent)
        current_len += len(sent) + 1

    if current:
        chunks.append(" ".join(current))

    return [c for c in chunks if c.strip()]


def chunk_document(
    text: str,
    max_chars: int = MAX_CHUNK_CHARS,
    min_chars: int = MIN_CHUNK_CHARS,
    is_markdown: bool = False,
) -> list[tuple[str, str]]:
    """
    Split document text into (section_title, chunk_body) pairs.

    Strategy:
      1. For markdown: split at heading boundaries first (each section = candidate chunk).
      2. Group paragraphs into chunks within max_chars.
      3. Single paragraphs exceeding max_chars are split at sentence boundaries.
      4. Chunks under min_chars are discarded (PDF headers, page numbers, stray lines).

    Returns: list of (subtitle, body) tuples, one tuple per intel item.
    """
    sections = _split_markdown_sections(text) if is_markdown else [("", text)]

    result: list[tuple[str, str]] = []

    for section_title, section_body in sections:
        paragraphs = [
            p.strip()
            for p in re.split(r"\n\s*\n", section_body)
            if p.strip()
        ]

        current_paras: list[str] = []
        current_len = 0

        for para in paragraphs:
            # Single paragraph exceeds max — flush, then sentence-split
            if len(para) > max_chars:
                if current_paras:
                    body = "\n\n".join(current_paras)
                    if len(body) >= min_chars:
                        result.append((section_title, body))
                    current_paras = []
                    current_len = 0
                for sub in _split_at_sentences(para, max_chars):
                    if len(sub) >= min_chars:
                        result.append((section_title, sub))
                continue

            # Adding this paragraph would overflow the chunk — emit current chunk
            if current_len + len(para) + 2 > max_chars and current_paras:
                body = "\n\n".join(current_paras)
                if len(body) >= min_chars:
                    result.append((section_title, body))
                current_paras = []
                current_len = 0

            current_paras.append(para)
            current_len += len(para) + 2  # +2 for the \n\n joiner

        # Emit remaining buffer for this section
        if current_paras:
            body = "\n\n".join(current_paras)
            if len(body) >= min_chars:
                result.append((section_title, body))

    return result


# ---------------------------------------------------------------------------
# Title inference
# ---------------------------------------------------------------------------

def _infer_title(path: Path) -> str:
    """Convert a filename into a human-readable title."""
    stem = path.stem
    title = re.sub(r"[-_]+", " ", stem)
    return title.title()


# ---------------------------------------------------------------------------
# Core ingest logic
# ---------------------------------------------------------------------------

def ingest_text(
    text: str,
    doc_title: str,
    source_url: str,
    published_at: Optional[datetime] = None,
    is_markdown: bool = False,
    trusted: bool = False,
    dry_run: bool = False,
) -> dict:
    """
    Chunk clean text, keyword-filter, score, and insert qualifying chunks
    into intel.db.

    trusted=True: inserts as 'llm_approved' (skips Stage 2 LLM filter).
                  Use for regulatory texts and verified institutional sources.
    dry_run=True: logs would-be insertions without writing to DB.

    Returns summary dict with counts.
    """
    if not text.strip():
        log.warning("  '%s' produced no text — skipping.", doc_title)
        return {
            "doc_title": doc_title,
            "chunks_total": 0, "inserted": 0,
            "skipped_keyword": 0, "duplicate": 0,
        }

    chunks = chunk_document(text, is_markdown=is_markdown)
    log.info("  Chunked into %d segment(s).", len(chunks))

    if len(chunks) > MAX_CHUNKS_PER_DOC:
        log.warning(
            "  [WARN] %d chunks exceeds MAX_CHUNKS_PER_DOC (%d). "
            "This is a large document — consider splitting it into sections.",
            len(chunks), MAX_CHUNKS_PER_DOC,
        )

    inserted = 0
    skipped_kw = 0
    duplicate = 0

    for i, (section_title, body) in enumerate(chunks):
        # Build item title: "Document — Section Title" or "Document — Part N of M"
        if section_title:
            item_title = f"{doc_title} — {section_title}"
        else:
            item_title = f"{doc_title} — Part {i + 1} of {len(chunks)}"

        full_text = f"{item_title} {body}"

        # Keyword pre-filter (same gate as RSS poller and Reddit adapter)
        if not has_any_keyword(full_text):
            skipped_kw += 1
            log.debug("    [skip-kw] %s", item_title[:65])
            continue

        cluster_tags = assign_clusters(full_text)
        if not cluster_tags:
            skipped_kw += 1
            continue

        score = pre_score(
            cluster_tags=cluster_tags,
            published_at=published_at,
        )

        item_id = make_item_id(SOURCE_TYPE, f"{source_url}::chunk_{i}")

        item = {
            "item_id":      item_id,
            "source":       SOURCE_TYPE,
            "title":        item_title[:300],
            "body":         body[:MAX_CHUNK_CHARS],
            "url":          source_url,
            "published_at": published_at.isoformat() if published_at else "",
            "author":       "",
            "cluster_tags": cluster_tags,
            "raw_score":    score,
            "meta": {
                "doc_title":    doc_title,
                "doc_url":      source_url,
                "chunk_index":  i,
                "total_chunks": len(chunks),
                "section":      section_title,
                "trusted":      trusted,
            },
        }

        # Dry-run: log and count, no DB writes
        if dry_run:
            log.info(
                "    [DRY] [%.1f] [%s] %s",
                score, ",".join(cluster_tags), item_title[:70],
            )
            inserted += 1
            continue

        # Dedup check
        if is_seen(item_id):
            duplicate += 1
            log.debug("    [dup] %s", item_title[:65])
            continue

        # Insert — always as 'pending' first (insert_item schema default)
        if insert_item(item):
            inserted += 1
            if trusted:
                # Promote immediately to 'llm_approved': skip Stage 2 LLM cost
                update_item_status(item_id, "llm_approved")
                log.info("  [+TRUSTED] [%.1f] [%s] %s", score, ",".join(cluster_tags), item_title[:65])
            else:
                log.debug("  [+] [%.1f] %s", score, item_title[:65])
        else:
            duplicate += 1

    return {
        "doc_title":       doc_title,
        "chunks_total":    len(chunks),
        "inserted":        inserted,
        "skipped_keyword": skipped_kw,
        "duplicate":       duplicate,
    }


def ingest_file(
    path: Path,
    title: Optional[str] = None,
    published_at: Optional[datetime] = None,
    trusted: bool = False,
    dry_run: bool = False,
) -> dict:
    """Ingest a single local file (PDF, TXT, or MD)."""
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported extension '{ext}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    doc_title  = title or _infer_title(path)
    source_url = path.as_uri()

    if published_at is None:
        mtime = path.stat().st_mtime
        published_at = datetime.fromtimestamp(mtime, tz=timezone.utc)

    log.info("Ingesting: %s", path.name)
    log.info("  Title: %s", doc_title)

    if ext == ".pdf":
        text     = extract_pdf_text(path)
        is_md    = False
    elif ext in (".md", ".markdown"):
        text     = path.read_text(encoding="utf-8")
        is_md    = True
    else:  # .txt
        text     = path.read_text(encoding="utf-8")
        is_md    = False

    text = _clean_text(text)
    log.info("  Extracted: %d characters", len(text))

    return ingest_text(
        text=text,
        doc_title=doc_title,
        source_url=source_url,
        published_at=published_at,
        is_markdown=is_md,
        trusted=trusted,
        dry_run=dry_run,
    )


def ingest_url(
    url: str,
    title: Optional[str] = None,
    published_at: Optional[datetime] = None,
    trusted: bool = False,
    dry_run: bool = False,
) -> dict:
    """Fetch a live web page and ingest its content."""
    log.info("Fetching: %s", url)
    page_title, text = extract_url_text(url)

    doc_title = title or page_title or url.rstrip("/").rsplit("/", 1)[-1]
    log.info("  Title: %s", doc_title)
    log.info("  Extracted: %d characters", len(text))

    return ingest_text(
        text=text,
        doc_title=doc_title,
        source_url=url,
        published_at=published_at or datetime.now(timezone.utc),
        is_markdown=False,
        trusted=trusted,
        dry_run=dry_run,
    )


# ---------------------------------------------------------------------------
# --list-docs summary query
# ---------------------------------------------------------------------------

def list_docs() -> None:
    """
    Print a status summary of all document-source items in intel.db,
    grouped by document title.
    """
    conn  = get_db()
    rows  = conn.execute(
        "SELECT meta_json, status, raw_score, created_at "
        "FROM intel_items WHERE source = 'document' "
        "ORDER BY created_at DESC"
    ).fetchall()
    conn.close()

    if not rows:
        print(
            "\nNo documents ingested yet.\n"
            "Run:  python doc_ingestor.py --file <path>  to begin Phase 1 loading.\n"
        )
        return

    # Group by doc_title from meta_json
    docs: dict[str, dict] = {}
    for row in rows:
        meta = json.loads(row["meta_json"] or "{}")
        dt   = meta.get("doc_title", "(unknown)")
        if dt not in docs:
            docs[dt] = {
                "pending": 0, "llm_approved": 0, "approved": 0,
                "rejected": 0, "skipped": 0, "total": 0,
                "top_score": 0.0, "ingested": row["created_at"][:10],
            }
        st = row["status"]
        docs[dt][st] = docs[dt].get(st, 0) + 1
        docs[dt]["total"]     += 1
        docs[dt]["top_score"]  = max(docs[dt]["top_score"], float(row["raw_score"]))

    header = f"  {'Document':<42} {'Date':>10} {'Chunks':>7} {'Pending':>8} {'Approved':>9} {'Top⬆':>6}"
    print(f"\n{header}")
    print("  " + "─" * 86)
    for dt, c in sorted(docs.items(), key=lambda x: x[1]["ingested"], reverse=True):
        print(
            f"  {dt[:41]:<41}  {c['ingested']:>10} {c['total']:>7} "
            f"{c['pending']:>8} {c['approved']:>9} {c['top_score']:>6.1f}"
        )
    total_chunks    = sum(d["total"]    for d in docs.values())
    total_approved  = sum(d["approved"] for d in docs.values())
    total_pending   = sum(d["pending"]  for d in docs.values())
    print(f"\n  {len(docs)} document(s) | {total_chunks} chunks total "
          f"| {total_pending} pending | {total_approved} approved\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="KritiKaal Intel Pipeline — Phase 1 Document Ingestor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Phase 1 workflow (one session at a time):
  1. python doc_ingestor.py --file docs/eudr.pdf --trusted   (trusted regulatory source)
  2. python doc_ingestor.py --dir docs/trade-reports/        (batch of trade PDFs)
  3. python llm_filter.py --run --limit 50                   (filter this session's batch)
  4. python hitl_review.py --run                             (human review)
  5. Repeat until approved count >= 150 across all clusters.

Trusted flag use cases (skip LLM filter, go straight to HITL):
  - Official regulatory texts: EUDR 2023/1115, UK DCTS guidance
  - Government tariff schedules and HS code tables
  - LWG audit standard documents
  - ITC / WTO official trade statistics PDFs

Do NOT use --trusted for:
  - Trade journal articles (use standard pipeline)
  - Reddit exports or user-generated content
  - Secondary analysis or opinion pieces
        """,
    )

    src = parser.add_mutually_exclusive_group()
    src.add_argument("--file",  metavar="PATH",
        help="Path to a single document (PDF, TXT, MD)")
    src.add_argument("--dir",   metavar="DIR",
        help="Ingest all supported files in a directory (non-recursive)")
    src.add_argument("--url",   metavar="URL",
        help="Fetch and ingest a web page (requires: pip install requests beautifulsoup4 lxml)")

    parser.add_argument("--title", metavar="TEXT",
        help="Override document title (default: inferred from filename or page <title>)")
    parser.add_argument("--date",  metavar="YYYY-MM-DD",
        help="Override published date (default: file mtime or today for URLs)")
    parser.add_argument("--trusted", action="store_true",
        help="Mark chunks llm_approved immediately — bypass LLM filter (for verified sources only)")
    parser.add_argument("--dry-run", action="store_true",
        help="Preview keyword matches and chunk structure without writing to DB")
    parser.add_argument("--list-docs", action="store_true",
        help="Show all ingested documents and chunk/status counts")
    parser.add_argument("--stats", action="store_true",
        help="Show full DB status breakdown across all sources")
    args = parser.parse_args()

    init_db()

    # ── list-docs ────────────────────────────────────────────────────────────
    if args.list_docs:
        list_docs()
        return

    # ── stats ─────────────────────────────────────────────────────────────────
    if args.stats:
        stats = db_stats()
        if not stats:
            print("Database is empty.")
        else:
            print("\nIntel Queue — Status Breakdown")
            print("=" * 45)
            grand_total = 0
            for status in ("pending", "llm_approved", "approved", "rejected", "skipped"):
                sources = stats.get(status, {})
                if sources:
                    n = sum(sources.values())
                    grand_total += n
                    src_str = ", ".join(f"{s}:{c}" for s, c in sorted(sources.items()))
                    print(f"  {status:<14} {n:>5}  ({src_str})")
            print(f"  {'TOTAL':<14} {grand_total:>5}")
        return

    # ── parse --date ──────────────────────────────────────────────────────────
    published_at: Optional[datetime] = None
    if args.date:
        try:
            published_at = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"ERROR: --date must be YYYY-MM-DD, got: {args.date}", file=sys.stderr)
            sys.exit(1)

    # ── single file ───────────────────────────────────────────────────────────
    if args.file:
        try:
            result = ingest_file(
                path=Path(args.file),
                title=args.title,
                published_at=published_at,
                trusted=args.trusted,
                dry_run=args.dry_run,
            )
        except (FileNotFoundError, ValueError, ImportError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)

        mode = " [DRY RUN]" if args.dry_run else ""
        status_note = " → llm_approved" if (args.trusted and not args.dry_run) else ""
        print(
            f"\n{result['doc_title']}{mode}{status_note}\n"
            f"  Chunks total : {result['chunks_total']}\n"
            f"  Inserted     : {result['inserted']}\n"
            f"  No signal    : {result['skipped_keyword']}\n"
            f"  Duplicates   : {result['duplicate']}\n"
        )
        if not args.dry_run and result["inserted"] > 0 and not args.trusted:
            print("Next: python llm_filter.py --run --limit 50")
        return

    # ── directory batch ───────────────────────────────────────────────────────
    if args.dir:
        dir_path = Path(args.dir)
        if not dir_path.is_dir():
            print(f"ERROR: Not a directory: {dir_path}", file=sys.stderr)
            sys.exit(1)

        files = sorted(
            f for f in dir_path.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        )
        if not files:
            print(
                f"No supported files found in: {dir_path}\n"
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )
            return

        print(f"Found {len(files)} file(s) in {dir_path}\n")
        total_inserted = 0
        total_skipped  = 0

        for idx, file_path in enumerate(files, 1):
            log.info("[%d/%d] %s", idx, len(files), file_path.name)
            try:
                result = ingest_file(
                    path=file_path,
                    published_at=published_at,
                    trusted=args.trusted,
                    dry_run=args.dry_run,
                )
                total_inserted += result["inserted"]
                total_skipped  += result["skipped_keyword"]
                print(
                    f"  [{idx}/{len(files)}] {file_path.name:<40} "
                    f"chunks:{result['chunks_total']:>3}  "
                    f"inserted:{result['inserted']:>3}  "
                    f"skipped:{result['skipped_keyword']:>3}"
                )
            except ImportError as exc:
                print(f"  [INSTALL] {exc}")
                sys.exit(1)
            except Exception as exc:
                log.warning("  [ERROR] %s: %s", file_path.name, exc)

            # Circuit breaker — halt before remaining files
            if total_inserted >= MAX_ITEMS_PER_RUN and idx < len(files):
                remaining = len(files) - idx
                print(
                    f"\n[CIRCUIT BREAKER] {total_inserted} items inserted this run "
                    f"(ceiling: {MAX_ITEMS_PER_RUN}). "
                    f"Halting before {remaining} remaining file(s).\n"
                    f"Run again to continue — already-ingested files will be skipped as duplicates."
                )
                break

        print(
            f"\nBatch complete\n"
            f"  Inserted : {total_inserted}\n"
            f"  Skipped  : {total_skipped}\n"
        )
        if not args.dry_run and total_inserted > 0 and not args.trusted:
            print("Next: python llm_filter.py --run --limit 50")
        return

    # ── URL ───────────────────────────────────────────────────────────────────
    if args.url:
        try:
            result = ingest_url(
                url=args.url,
                title=args.title,
                published_at=published_at,
                trusted=args.trusted,
                dry_run=args.dry_run,
            )
        except (ImportError, Exception) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)

        mode = " [DRY RUN]" if args.dry_run else ""
        status_note = " → llm_approved" if (args.trusted and not args.dry_run) else ""
        print(
            f"\n{result['doc_title']}{mode}{status_note}\n"
            f"  Chunks total : {result['chunks_total']}\n"
            f"  Inserted     : {result['inserted']}\n"
            f"  No signal    : {result['skipped_keyword']}\n"
            f"  Duplicates   : {result['duplicate']}\n"
        )
        if not args.dry_run and result["inserted"] > 0 and not args.trusted:
            print("Next: python llm_filter.py --run --limit 50")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
