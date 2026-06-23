# /daily-scout — KritiKaal Authority Engine
# Sequential execution: S6 → S7 → S8
# Trigger: Daily — recommended before 09:00 UK
# CEO time during run: zero
# CEO review + posting time: ≤20 minutes

You are executing the daily KritiKaal Authority Engine scouting run. This is a fully autonomous, sequential, single-session execution. Do NOT pause for user input between steps. Run all three steps in order and deliver the final social brief to the social-queue folder before confirming completion.

---

## Pre-Flight Checks (complete before Step 1)

1. Record today's date in YYYY-MM-DD format and current UK time.
2. Check `B-brain/06-growth/data-feeds/reddit-signals.json` — note: LIVE (with timestamp) or FALLBACK.
3. Check `B-brain/06-growth/data-feeds/linkedin-signals.json` — note: LIVE or FALLBACK.
4. Read `B-brain/06-growth/social-queue/README.md` for current 9:1 ratio and karma tracker.
5. Check `B-brain/06-growth/social-queue/` for any files from previous days marked with unposted drafts.
6. Confirm `B-brain/06-growth/social-queue/` folder exists. Create if not.

---

## Execution Sequence — Do Not Pause Between Steps

### STEP 1 — S6: Daily Scout
Read full spec: `B-brain/06-growth/agents/S6-daily-scout.md`
Read data inputs:
  - `B-brain/06-growth/data-feeds/reddit-signals.json`
  - `B-brain/06-growth/data-feeds/linkedin-signals.json`
  - `B-brain/06-growth/social-queue/README.md` (9:1 ratio + karma status)
Execute: Score and filter all opportunities to top 5 maximum. Run Reddit account health check.
If data feeds are not live: switch to Manual Scout Prompt mode per S6 spec.
Hold complete S6 output in working memory. Proceed immediately to Step 2.

### STEP 2 — S7: Content Forge
Read full spec: `B-brain/06-growth/agents/S7-content-forge.md`

**MANDATORY: Read all four voice calibration documents before drafting a single word:**
  1. `B-brain/06-growth/01-voice-dna-v2.md`
  2. `B-brain/06-growth/02-voice-cheat-sheet.md`
  3. `B-brain/06-growth/content/vsl-teleprompter-FINAL.md`
  4. `B-brain/06-growth/content/article-01-eudr-india-leather-PUBLICATION-READY.md`

Input: S6 opportunity list from working memory.
Execute: Write one platform-native draft per opportunity. Apply 9:1 ratio status from S6. Match Yossi Daniel's voice from calibration documents — not generic B2B tone.
Hold all S7 drafts in working memory. Proceed immediately to Step 3.

### STEP 3 — S8: Humanization Layer
Read full spec: `B-brain/06-growth/agents/S8-humanization-layer.md`
Input: S7 drafts from working memory.

**MANDATORY SEQUENCE — apply to every draft:**
1. Strip transition scaffolding (Furthermore, Moreover, It's worth noting, etc.)
2. Break parallel structure (no two consecutive matched-construction sentences)
3. Inject one voice-specific anchor (2012 story element, AQL detail, or EUDR documentation moment)
4. Introduce one deliberate fragment or trailing thought
5. Replace all hedges with direct statements or silence
6. Verify at least one specific number is present

Then: Submit each draft to GPTZero API for human score.
- ≥85% human: cleared — advance
- 70–84%: flag specific sentences, suggest targeted edits
- <70%: rewrite flagged sentences, re-check — if still <70%, return to S7

Hold final S8 output. Proceed to Output Protocol.

---

## Output Protocol

1. Write the complete social brief to:
   `B-brain/06-growth/social-queue/[YYYY-MM-DD]-social-drafts.md`

2. Brief structure:
```markdown
# Daily Social Brief — [DATE]
# KritiKaal Authority Engine | /daily-scout

Data feeds: Reddit [LIVE/FALLBACK] | LinkedIn [LIVE/FALLBACK]
Reddit 9:1 status this week: [X genuine : X promotional] — [GREEN / AMBER / RED]
Reddit karma this week: +[X] | Running total: ~[X]
Opportunities identified: [X]
Drafts ready for CEO: [X]
Estimated CEO time: ~[X] minutes

---

[DRAFT 1 — full S8 output block]

[DRAFT 2 — full S8 output block]

[... up to 5 drafts]

---

## CEO Action Checklist

[ ] Read all drafts above (~5 min)
[ ] Edit any marked "CEO EDIT REQUIRED: Yes" — add one personal detail (~2 min each)
[ ] Select which to post today
[ ] Post manually — home IP, no VPN, direct to platform
[ ] Mark each posted draft: POSTED [time]
[ ] Update karma tracker: social-queue/README.md (+X karma from today's activity)
[ ] Note any KritiKaal mentions posted (for 9:1 ratio update)
```

3. Confirm completion to user in exactly this format:
```
DAILY SCOUT COMPLETE — [DATE]
Brief: B-brain/06-growth/social-queue/[DATE]-social-drafts.md
Drafts ready: [X]
Reddit account health: [GREEN / AMBER / RED]
CEO time required: ~[X] minutes
GPTZero scores: [list each draft score, e.g. "Draft 1: 91% | Draft 2: 87% | Draft 3: 84% FLAGGED"]
```

---

## Failure Protocol

If any step fails:
- Note the failure and reason
- Continue with remaining steps using available data
- Flag in the brief header: "STEP [X] PARTIAL — [reason]"
- Do not abort the session. A partial brief is better than none.

If GPTZero API is unavailable:
- Apply the six-point humanization protocol manually
- Note in brief: "GPTZero API unavailable — humanization protocol applied, score unverified"
- Flag drafts as "UNVERIFIED — CEO should review extra carefully before posting"

---

## Reddit Safety Reminders (display at top of every brief)

1. Post manually from your home network. No VPN on the Reddit session.
2. Never use vote manipulation — do not upvote your own comments from any account.
3. Never visit karma farm subreddits (r/freekarma4u, etc.) — instant CQS drop.
4. If 9:1 ratio is RED, do not post any KritiKaal-adjacent content today regardless of opportunity quality.
5. Warm-up mode (Weeks 1–2): post in permeable subreddits only — see S6 for subreddit map.

---

*Daily Scout Trigger | KritiKaal Authority Engine | Option 1 — Sequential Execution | Deployed 2026-04-25*
