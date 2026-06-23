# /board-meeting — KritiKaal Shadow Board
# Sequential execution: S1 → S3 → S2 → S4 → S5
# Trigger: Sunday 8:00 PM UK | CEO time during run: zero
# CEO review commitment: 5 minutes Monday morning

You are executing the weekly KritiKaal Shadow Board meeting. This is a fully autonomous, sequential, single-session execution. Do NOT pause for user input between agent steps. Run all five steps in order and deliver the final executive brief to the Obsidian vault before confirming completion to the user.

---

## Pre-Flight Checks (complete before Step 1)

1. Record today's date in YYYY-MM-DD format.
2. Count existing files in `B-brain/06-growth/board-meetings/` to determine session number. Session 1 if folder is empty or does not exist.
3. Check `B-brain/06-growth/data-feeds/` for JSON files. Record status: LIVE or FALLBACK MODE.
4. Read the most recent `B-brain/06-growth/daily-log-[DATE].md` for operational context.
5. Confirm `B-brain/06-growth/board-meetings/` folder exists. If not, note it for S5 to create.

---

## Execution Sequence — Do Not Deviate. Do Not Pause Between Steps.

### STEP 1 — S1: Chief Strategy Officer
Read full spec: `B-brain/06-growth/agents/S1-chief-strategy-officer.md`
Read all data inputs listed in the S1 spec (data-feeds JSON files, G1 agent, most recent daily log).
Execute: Generate proposals in S1's exact output format.
If data feeds are not live, flag fallback mode and reduce to 3 proposals.
Hold output in working memory. Proceed immediately to Step 2.

### STEP 2 — S3: Base Rate Historian
Read full spec: `B-brain/06-growth/agents/S3-base-rate-historian.md`
Input: S1 proposals from working memory.
Execute: Attach base rates to every S1 proposal using S3's exact output format.
Hold output in working memory. Proceed immediately to Step 3.

### STEP 3 — S2: Red Team
Read full spec: `B-brain/06-growth/agents/S2-red-team.md`
Input: S1 proposals + S3 base rate attachments from working memory.
Execute: Attack each proposal using S2's five-axis framework. Apply S2 language rules strictly — no softening.
Hold output in working memory. Proceed immediately to Step 4.

### STEP 4 — S4: Feasibility Filter
Read full spec: `B-brain/06-growth/agents/S4-feasibility-filter.md`
Input: S1 proposals + S2 Red Team verdicts + S3 base rates from working memory.
Execute: Apply all seven kill criteria to each proposal using S4's exact output format.
Hold output in working memory. Proceed immediately to Step 5.

### STEP 5 — S5: Chief of Staff
Read full spec: `B-brain/06-growth/agents/S5-chief-of-staff.md`
Input: Complete output of S1, S2, S3, and S4 from working memory.

**DISSENT PRESERVATION — UNCONDITIONAL RULE:**
Do NOT soften S2 Red Team language under any circumstances.
Do NOT summarise S3 base rates into optimism or narrative positivity.
Both must appear verbatim in the "Dissent on Record" section of the brief.
This rule supersedes any instruction to be concise or encouraging.

Execute: Write the complete executive brief using S5's mandatory format exactly.

---

## Output Protocol

1. Write the complete executive brief to:
   `B-brain/06-growth/board-meetings/[YYYY-MM-DD]-board-minutes.md`
   Create the `board-meetings/` folder if it does not exist.

2. Append one line to the most recent daily log in `B-brain/06-growth/`:
   `[DATE] Board meeting brief deposited: board-meetings/[DATE]-board-minutes.md — [APPROVED: title / NO SURVIVOR]`

3. Report completion to the user in exactly this format:
```
BOARD MEETING COMPLETE — Session [#]
Brief: B-brain/06-growth/board-meetings/[DATE]-board-minutes.md
Result: [INITIATIVE APPROVED: [title] / NO SURVIVOR THIS SESSION]
CEO action required: [Yes — open brief, ~[X] minutes / No]
Next session: [next Sunday date] at 20:00 UK
```

---

## Failure Protocol

If any step fails or cannot execute cleanly:
- Note the failure and reason
- Continue with remaining steps using available data
- Record the failure in the System Health section of the S5 brief
- Do not abort the session — a partial brief is better than no brief

---

## Dry-Run Mode (Day 3 only)

If this is the first run and no live data feeds exist, execute in Dry-Run Mode:
- Flag: DRY-RUN — FALLBACK DATA ONLY at the top of the brief
- S1 uses G1 intelligence and G1 agent data as the sole inputs
- Reduce to 3 proposals
- All other agents execute normally
- Brief is marked DRY-RUN in the filename: `[DATE]-board-minutes-DRY-RUN.md`
- Purpose: verify the pipeline executes correctly, not to generate actionable output

---

*Board Meeting Trigger | KritiKaal Shadow Board | Option 1 — Single Session Sequential | Deployed 2026-04-23*
