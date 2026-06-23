# Social Queue — Karma Tracker & Ratio Log
# KritiKaal Authority Engine
# Version: 1.0 | Created 2026-04-30

## Purpose

This file is S6's primary data source for:
1. **9:1 ratio enforcement** — GREEN / AMBER / RED status for every session
2. **Weekly karma progress** — reported at the top of every daily brief
3. **Shadowban check reminders** — flagged every Friday by S6, logged here by CEO

**S6 reads this file at the start of every /daily-scout session.**
**CEO maintains this file — log every post within 24 hours of posting.**
No agent writes to this file. S6 reads it. Yossi writes to it.

---

## Reddit Account Details

| Field | Value |
|---|---|
| Username | *(enter when account created)* |
| Account created | *(enter date — the 60-day clock starts here)* |
| Email verified | [ ] |
| Phone verified | [ ] |
| CQS status | New → Moderate (after email + phone) → Established (60+ days, 100+ karma) |
| Current CQS | Not started |

---

## 9:1 Ratio — CURRENT STATUS

**Rule:** For every 1 KritiKaal-adjacent post, there must be at least 9 genuine contributions with no KritiKaal mention.

**S6 reads this block directly. Keep it updated after every post.**

```
CURRENT RATIO STATUS: NOT STARTED
Genuine posts this week: 0
Promotional posts this week: 0
Running ratio: N/A
```

**Status key:**
- GREEN — ratio better than 9:1 (e.g., 18:1, 27:1) — all content types permitted
- AMBER — approaching 8:1 — suppress KritiKaal mention on Reddit even if S6 flagged YES. LinkedIn posts may proceed with anti-pitch close.
- RED — at or worse than 9:1 — zero KritiKaal mentions on any platform. Notify S8 to flag in CEO brief.
- NOT STARTED — no posts logged yet — S6 defaults to AMBER protocol until first genuine post is logged.

**If this file has no entry in the last 7 days:** S6 reports UNKNOWN and enforces AMBER protocol automatically.

---

## How to Log a Post

After every post to Reddit or LinkedIn — add one row to the current week's table within 24 hours.

| Column | What to enter |
|---|---|
| Date | YYYY-MM-DD |
| Platform | Reddit / LinkedIn |
| Location | r/subredditname or LinkedIn Comment or LinkedIn Post |
| Post Type | GENUINE (no KritiKaal mention) / PROMOTIONAL (KritiKaal mentioned or linked) |
| Karma | Check 24-48 hours after posting — upvotes (Reddit) or reactions (LinkedIn) |
| URL | Direct permalink to the comment or post |
| Notes | Optional: GPTZero score, thread topic, follow-up replies received |

---

## Weekly Post Log

### Week 1 — Start date: ___________

| Date | Platform | Location | Post Type | Karma | URL | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |

**Week 1 summary:**
- Genuine: 0 | Promotional: 0 | Ratio: — | Status: NOT STARTED
- Karma earned this week: 0
- Running karma total: 0
- Phase 2 criteria progress: 0/4

---

### Week 2 — Start date: ___________

| Date | Platform | Location | Post Type | Karma | URL | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |

**Week 2 summary:**
- Genuine: 0 | Promotional: 0 | Ratio: — | Status: NOT STARTED
- Karma earned this week: 0
- Running karma total: 0
- Phase 2 criteria progress: 0/4

---

*[Copy the week template above when each new week begins. Do not delete old weeks — they are the ratio record.]*

---

## Shadowban Check Protocol

**S6 flags this reminder every Friday session, without exception.**

**Steps (5 minutes):**
1. Open a private / incognito browser window — do not log in to Reddit
2. Visit: `https://www.reddit.com/user/[your_username]/` (replace with actual username)
3. Posts visible = account healthy
4. "Nobody on Reddit goes by that name" OR posts invisible = shadowban confirmed

**If shadowbanned:**
- Stop all posting immediately
- Do NOT create a new account from the same IP address
- Post in r/modsupport explaining the situation
- Visit: https://www.reddit.com/appeals
- Report to Adam immediately — all /daily-scout output pauses until resolved

**Shadowban check log:**

| Date | Checked | Result | Action taken |
|---|---|---|---|
| | | | |
| | | | |

---

## Warm-Up Phase Protocol (Weeks 1-8)

Reddit account requires 60-90 days of genuine engagement before posting in primary subreddits. Do not shortcut this. CQS account trust is built slowly and destroyed instantly.

| Phase | Weeks | Subreddits | Post type | KritiKaal allowed? |
|---|---|---|---|---|
| Warm-up | 1-2 | r/AskUK, r/CasualConversation, r/UKFoods, r/unitedkingdom | Genuine only — no leather/manufacturing content | No |
| Transition | 3-4 | Above + r/Entrepreneur, r/smallbusiness | Genuine — light professional topics ok | No |
| Primary prep | 5-8 | Above + r/ecommerce, r/supplychain (observe only) | Genuine — can answer in subject area | No |
| Primary active | 9+ | r/supplychain, r/manufacturing, r/ecommerce, r/leather | Expert engagement per S7 spec | Yes (GREEN only) |

---

## Karma Milestone Tracker

Track progress toward Phase Graduation (see S6 for full criteria):

| Milestone | Target | Achieved | Date |
|---|---|---|---|
| Reddit account created | Account exists | [ ] | |
| Email + phone verified (CQS: Moderate) | Both done | [ ] | |
| First post in any warm-up sub | 1 post | [ ] | |
| 50 karma on account | 50+ karma | [ ] | |
| First post in r/supplychain or r/manufacturing | 1 post | [ ] | |
| 3 posts with >10 upvotes in target subs | 3 posts | [ ] | |
| 4-week rolling period with zero AMBER/RED flags | 4 clean weeks | [ ] | |
| 10 consecutive GPTZero scores 85%+ | 10 drafts | [ ] | |
| Phase 2 graduation — all 4 criteria met | CEO decision | [ ] | |

---

## S6 Quick Reference — What S6 Reports

When S6 reads this file at session start, it outputs:

```
Reddit 9:1 ratio this week: [X genuine : X promotional] — [GREEN / AMBER / RED / UNKNOWN]
Reddit karma this week: +[X] | Running total: ~[X]
Shadowban check: [Due today (Friday) / Last checked: DATE — result: OK]
```

If file is missing or all log tables are empty: S6 reports UNKNOWN, enforces AMBER protocol, and includes:
"NOTICE: social-queue/README.md has no post entries. Ratio tracking inactive. KritiKaal mentions suppressed until log is updated by CEO."

---

*Social Queue Karma Tracker | KritiKaal Authority Engine | Created 2026-04-30*
*CEO maintains this file. S6 reads it. No agent writes to it.*
