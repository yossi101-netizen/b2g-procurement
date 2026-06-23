# MIGRATION PLAN — YouTube Authority Engine
**Workspace:** `C:\Users\mygre\Documents\yossi-workspace`
**Framework:** ABC-TOM
**Status:** ⏳ Awaiting manual file move
**Created:** 2026-05-06

---

## 1. Project Context

### What Is the YouTube Authority Engine?
The YouTube Authority Engine is a content intelligence sub-system designed to feed **KritiKaal**'s B2B demand-generation pipeline. KritiKaal (KritiKaal.com) operates as a managed manufacturing and wholesale platform. Its target buyers are Israeli B2B volume purchasers — importers, OEM brands, distributors, and private-label operators.

The engine solves a specific problem: **finding and extracting the exact pain-language B2B buyers use when discussing manufacturing, sourcing, and supplier failures** — language that would otherwise require hundreds of hours of manual research.

### How It Works (3-Stage Pipeline)
```
Stage 1 — EXTRACTION
  YouTube channels (manufacturing / sourcing / supply-chain niche)
  └── extract_insight.py pulls transcripts via youtube-transcript-api
      └── Raw transcript saved to B-brain/04-INBOX/youtube-research/

Stage 2 — ANALYSIS
  youtube-analyst-agent.md runs against the raw transcript
  └── Outputs structured pain-point clusters keyed to KritiKaal's ICP
      └── Findings written into C-core/04-youtube-pain-matrix.md

Stage 3 — HUMANIZATION & DISTRIBUTION
  Pain-point copy fed into Otterly.ai for humanized content generation
  └── Output: LinkedIn posts, email hooks, landing-page copy
      └── Targeting managed manufacturing / sourcing decision-makers
```

### Strategic Objective
Map the exact vocabulary B2B buyers use to describe their pain, so every piece of KritiKaal content sounds written by someone who has lived those problems — not by a marketing team guessing at them.

---

## 2. Pre-Move: Create Target Directories

**Run these commands before moving any files.** They create the folders that don't exist yet in the ABC-TOM structure.

```bash
# From workspace root
cd "C:\Users\mygre\Documents\yossi-workspace"

# B-brain: INBOX for raw research
mkdir -p "B-brain/04-INBOX/youtube-research"

# T-tools: skill module for the extraction script
mkdir -p "T-tools/01-skills/youtube-extraction"
```

> **Note:** `C-core/` and `A-agents/` already exist. Files dropped there need no directory creation.

---

## 3. File Mapping: YOUTUBE → ABC-TOM

Move each file from `YOUTUBE\` to its canonical destination as follows.

### 3.1 Strategic Intelligence — C-Core (Business DNA)

| Source file (in YOUTUBE\) | Destination |
|---|---|
| `Strategic Intelligence Brief (Pain Matrix).*` | `C-core/04-youtube-pain-matrix.md` |
| Any file with "pain", "ICP", "audience insight" in name | `C-core/04-youtube-pain-matrix.md` |

**Why C-core?** The Pain Matrix is a strategic document — it shapes what KritiKaal says and to whom. It belongs next to `01-business-context.md` and `02-target-audience.md` as Core DNA, not in a tool folder.

**Rename rule:** Whatever the source file is named, the destination is always `04-youtube-pain-matrix.md`. The numbering (04) places it after the existing core files chronologically.

---

### 3.2 Agent Definition — A-Agents (Agent Roster)

| Source file (in YOUTUBE\) | Destination |
|---|---|
| `youtube-analyst-agent.md` | `A-agents/youtube-analyst-agent.md` |

**Why A-agents?** Agent definitions live here alongside `01-architect-agent.md`. This file defines the YouTube Analyst Agent's persona, instructions, and prompt templates.

**Keep the filename as-is.** No renaming needed.

---

### 3.3 Extraction Script — T-Tools (Skill Module)

| Source file (in YOUTUBE\) | Destination |
|---|---|
| `extract_insight.py` | `T-tools/01-skills/youtube-extraction/extract_insight.py` |

**Why this sub-path?**
`T-tools/` holds all operational scripts. `01-skills/` groups atomic, reusable skill scripts (as opposed to full agents). `youtube-extraction/` namespaces this skill so it doesn't collide with future skills (e.g., `reddit-extraction/`, `linkedin-extraction/`).

**If there is an associated `__init__.py`, `config.json`, or `.env.example`**, drop those into `T-tools/01-skills/youtube-extraction/` alongside the script.

---

### 3.4 Raw Research — B-Brain INBOX

| Source content type | Destination |
|---|---|
| Reddit thread screenshots or exports | `B-brain/04-INBOX/youtube-research/` |
| Raw YouTube transcripts (`.txt`, `.json`) | `B-brain/04-INBOX/youtube-research/` |
| Channel notes, scratchpad research | `B-brain/04-INBOX/youtube-research/` |
| Any file that is not a script, agent, or strategy doc | `B-brain/04-INBOX/youtube-research/` |

**Why INBOX?** B-brain/INBOX is the unprocessed-intelligence staging area. Files here are raw material — they haven't been synthesized into a strategic document yet. Once the YouTube Analyst Agent processes them and updates `C-core/04-youtube-pain-matrix.md`, the raw files can stay as reference or be archived.

**Naming convention for INBOX files:**
```
YYYYMMDD_[source-type]_[topic-slug].txt
Example: 20260506_reddit_manufacturing-sourcing-pain.txt
         20260506_transcript_channel-name-video-slug.txt
```

---

## 4. Post-Move File Tree (Expected State)

After completing the moves above, the ABC-TOM structure should look like this:

```
yossi-workspace/
├── A-agents/
│   ├── 01-architect-agent.md          (existing)
│   └── youtube-analyst-agent.md       ← MOVED FROM YOUTUBE\
│
├── B-brain/
│   ├── 01-tech-stack.md               (existing)
│   └── 04-INBOX/
│       └── youtube-research/          ← NEW DIRECTORY
│           ├── [reddit threads]       ← MOVED FROM YOUTUBE\
│           └── [raw transcripts]      ← MOVED FROM YOUTUBE\
│
├── C-core/
│   ├── 01-business-context.md         (existing)
│   ├── 02-target-audience.md          (existing)
│   └── 04-youtube-pain-matrix.md      ← MOVED FROM YOUTUBE\
│
├── T-tools/
│   ├── 01-skills/                     ← NEW DIRECTORY
│   │   └── youtube-extraction/        ← NEW DIRECTORY
│   │       └── extract_insight.py     ← MOVED FROM YOUTUBE\
│   ├── [existing scripts...]
│
├── MIGRATION_PLAN_YOUTUBE.md          ← THIS FILE
└── requirements.txt                   ← NEEDS UPDATE (see Section 5)
```

---

## 5. Dependency Update — requirements.txt

**Current contents:**
```
openai
python-dotenv
aiohttp
beautifulsoup4
openpyxl>=3.1
```

**Updated contents (add these two lines):**
```
youtube-transcript-api>=0.6.2
requests>=2.31.0
```

**Full updated `requirements.txt`:**
```
openai
python-dotenv
aiohttp
beautifulsoup4
openpyxl>=3.1
youtube-transcript-api>=0.6.2
requests>=2.31.0
```

**Why these packages:**
- `youtube-transcript-api` — pulls auto-generated and manual captions from YouTube without needing the YouTube Data API. Used by `extract_insight.py`.
- `requests` — standard HTTP client for calling the Otterly.ai API endpoint (humanization layer). `aiohttp` exists but `requests` is simpler for synchronous one-off API calls in the extraction script.

**Install command:**
```bash
cd "C:\Users\mygre\Documents\yossi-workspace"
venv\Scripts\activate
pip install youtube-transcript-api>=0.6.2 requests>=2.31.0
```

---

## 6. Verification Checklist

Run through this after completing all moves:

```
[ ] B-brain/04-INBOX/youtube-research/   — directory exists
[ ] T-tools/01-skills/youtube-extraction/ — directory exists
[ ] C-core/04-youtube-pain-matrix.md     — file present
[ ] A-agents/youtube-analyst-agent.md    — file present
[ ] T-tools/01-skills/youtube-extraction/extract_insight.py — file present
[ ] requirements.txt                     — updated with two new packages
[ ] YOUTUBE\ folder                      — empty (safe to delete)
```

Once all boxes are checked, the `YOUTUBE\` folder can be safely deleted.

---

## 7. Next-Step Prompt (Ready to Copy)

Once you have manually moved all files per the mapping above, paste this prompt to begin the next phase:

---

```
Context: I have completed the YouTube Authority Engine migration into the ABC-TOM workspace.

All files are now in their canonical locations:
- C-core/04-youtube-pain-matrix.md         (Strategic Pain Matrix)
- A-agents/youtube-analyst-agent.md        (YouTube Analyst Agent)
- T-tools/01-skills/youtube-extraction/extract_insight.py  (Extraction Script)
- B-brain/04-INBOX/youtube-research/       (Raw research files)
- requirements.txt                         (Updated with youtube-transcript-api + requests)

The YOUTUBE\ folder has been deleted.

Your task:
1. Read C-core/04-youtube-pain-matrix.md in full.
2. Read A-agents/youtube-analyst-agent.md in full.
3. Based on the pain-points and ICP signals in those files, design and build the Script-Generation Module — Phase 2 of the YouTube Authority Engine. This module must:
   a. Accept a pain-point cluster from the Pain Matrix as input.
   b. Generate a structured script brief (hook, body, CTA) written in the voice of a KritiKaal B2B manufacturing authority — not a generic content creator.
   c. Output the brief in a format ready to feed into Otterly.ai for humanization.
4. Create the associated Copywriter Agent definition at A-agents/copywriter-agent.md — define its persona, constraints, and the exact prompt template it uses when generating script briefs.
5. Save the Script-Generation Module script at T-tools/01-skills/script-generation/generate_script.py.

Do not guess at the pain-points or KritiKaal's voice — read the files first, then build.
```
