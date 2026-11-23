---
description: The FEAT's Closure section that sdd-review writes — rows, outcome line, retro numbers and the calibration behind the trimmed checks.
kind: detail
---

# Closure record

`sdd-review` writes it into the FEAT under `## Closure`, or, in a FEAT with `## Versions`, under the open block's `#### Closure` (the `spec-feature.md` template carries the heading), then runs `spec_trace.py validate`, which refuses a closure without the outcome line or without a measured Result in a table headed `Check | Command or measurement | Result` (case-insensitive, spaces trimmed). A Result starting with `not run` blocks `validated`; it stays legal with `delivered` or `returned:`.

## Shape

```markdown
## Closure

Main: 1a2b3c4 · 2026-11-20 · reviewer provider=claude tier=opus session=<id> · outcome validated

| Check | Command or measurement | Result |
|---|---|---|
| Task proofs | `review_checks.py feat-proofs --feat … --run` | 9 pass; T1 stale (`content-projection/` merged into `content-publish/`, #4036), re-pointed, pass |
| Lint | `spec_trace.py lint docs/spec FEAT-109` | 8 stale items fixed (Not verified, Audit Pending, 3 `[PROPOSAL]` → folded into Scope, …) |
| Trace | same lint | REQ-F-997: `HaircutRefundMigrationIT` linked in J-12 S4 |
| Enablers | `spec_trace.py enablers docs/spec --feat FEAT-109`, `spec_trace.py check docs/spec` | `enablers: OK (3 enablers, 7 contracts)`; check OK |
| Broad suite | record of wave 3: `./mvnw -B -ntp verify` at 1a2b3c4 | pass (reused) |
| REQ-NF-003 p95 latency ≤ 50 ms | measured 31 ms, `k6 run trade.js` on hml, 2026-11-20 | pass |
| REQ clauses → tests | model reading, each "untested" grep-checked | 2 missing tests filed as T11, T12 |
| J-12 S5 manual | owner, 2026-11-20 | pass |
| Playtest (with `sdd.passes`, greybox block) | the History line `- 2026-11-20 playtest: 0.3 greybox at 1a2b3c4 — go — owner: "…"` (`playtest.md`) | go |

Retro: blocked rows 1 (T5, spec gap) · review rounds 9 over 6 PRs, max 3 on T4 · REQs amended after planned 1 (REQ-F-015)
```

- The Enablers row exists only with `docs/spec/enablers/`; the `traceability.md` that `generate` rewrites after `validate` is each ENB's History and lands in the same commit.
- One row per check; a check that could not run is `not run: <why>` and blocks `validated`. Missing-test rows do not.
- The outcome is `validated`, `delivered (release: merge)` or `returned: <the rows, spec PRs, owner questions, clarify, NEED or DEBT it filed>`. A returned closure is rewritten on the next run, never appended below the old one.
- Results are measured, with the command; targets and estimates are labeled `planned:` and never fill the Result column.

## Retro numbers

| Number | Counts | Command or source |
|---|---|---|
| Blocked rows | task rows that went blocked at least once | the items' history (issue events or the TASK files' log), or `[BLOCKER]` comments |
| Review rounds | delivery verdicts across the FEAT's PRs, and the most on one PR | the PRs' review records or the loop ledger |
| REQs amended after planned | REQ files listed by the FEAT changed after the FEAT's `planned` date | `git log --since=<planned date> --format=%h -- <REQ files>` |

## Calibration

[FACT] KIT-069 calibration, 2026-11-14, on 5 delivered FEATs of a consumer at its `main` `606a2f6f9`: every FEAT had findings and none was a product defect. 0 of 3,263 server and client tests failed. 3 of 5 FEATs had a proof command rotted by a later PR (a merged folder, a renamed content id, a moved Godot script that exits 0 while loading nothing). Reading found 16 stale-text items over 5 of 5 FEATs, and 4 untested plus 5 partly covered of 61 counterexample clauses; 1 of 3 grep spot checks of "untested" was wrong. So the proofs, stale text and trace are scripts, the separate REQ re-run is dropped for the wave's broad suite, and the clause mapping lists missing tests without blocking.

What would prove this wrong: a larger sample in which the dropped REQ re-run finds a real `main` failure that the wave's broad suite missed. That would restore the re-run as a script.
