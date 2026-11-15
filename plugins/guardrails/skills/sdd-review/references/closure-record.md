---
description: The FEAT's Closure section that sdd-review writes — table rows, outcome line and the retro numbers with the commands that count them.
kind: detail
---

# Closure record

`sdd-review` writes it into the FEAT under `## Closure` (the `spec-feature.md` template carries the heading), then runs `spec_trace.py validate`, which refuses a FEAT whose closure holds no line.

## Shape

```markdown
## Closure

Main: 1a2b3c4 · 2026-11-20 · reviewer provider=claude tier=opus session=<id> · outcome validated

| Check | Command or measurement | Result |
|---|---|---|
| CA-1 | `./mvnw -q -Dtest=TradeServiceTest test` | pass (12 tests) |
| REQ-F-014 example | `TradeServiceTest#acceptsMatchingOffer` | pass |
| REQ-F-014 counterexample | `TradeServiceTest#refusesExpiredOffer` | pass |
| REQ-NF-003 p95 latency ≤ 50 ms | measured 31 ms, `k6 run trade.js` on hml, 2026-11-20 | pass |
| J-07 S1–S4 | `game/client/tests/trade/test_flow.gd`; S4 manual: owner, 2026-11-20 | pass |
| CA-4 (stale proof) | cited `server/src/test/.../OldTest.java` moved in #812; ran `TradeOfferTest` | pass, path corrected |
| Broad suite | `./mvnw -q verify` | pass |
| Decisions | `[DECISION]` 2026-11-03 → folded into CA-2; "until T7 lands" deleted (T7 merged, #790) | 2 reconciled |

Retro: blocked rows 1 (T5, spec gap) · review rounds 9 over 6 PRs, max 3 on T4 · REQs amended after planned 1 (REQ-F-015)
```

- One row per check; a check that could not run is `not run: <why>` and blocks `validated`.
- The outcome is `validated`, `delivered (release: merge)` or `returned: <the rows, clarify, NEED or DEBT it filed>`. A returned closure is rewritten on the next run, never appended below the old one.
- Results are measured, with the command; targets and estimates are labeled `planned:` and never fill the Result column.

## Retro numbers

| Number | Counts | Command or source |
|---|---|---|
| Blocked rows | task rows that went blocked at least once | the items' history (issue events or the TASK files' log), or `[BLOCKER]` comments |
| Review rounds | delivery verdicts across the FEAT's PRs, and the most on one PR | the PRs' review records or the loop ledger |
| REQs amended after planned | REQ files listed by the FEAT changed after the FEAT's `planned` date | `git log --since=<planned date> --format=%h -- <REQ files>` |

The numbers feed the process falsifiers: REQ amendments after `planned` should drop as clarify improves, and review rounds per PR should not rise.
