---
description: The greybox playtest under sdd.passes — who plays, the History line the owner signs, each outcome.
kind: detail
---

# Playtest record

Under `sdd.passes: [greybox, polish]` (KIT-094) a new mechanic is one FEAT with two version blocks, `### <version> greybox` then `### <version> polish` (skill `sdd-plan` § 3). The greybox block is accepted by a playtest, not by captures: placeholder art has no mock, so `evidence.visual_approval` and row rule j do not apply to its rows (skill `review` § 2, `../../sdd-tasks/references/row-checks.md`). With `passes: []`, the default, nothing here applies.

## When and who

- After the greybox block's last row merged and the closure scripts pass on `main` (SKILL §§ 1–3), before `validate` without `--check`.
- The owner alone plays the build of the closure commit, locally or on the test environment. A reviewer, an agent or a friends' session never signs it; a friends' playtest is release acceptance (skill `sdd-release` § 4).
- The owner judges the rules and the feel against the REQs' tunable values; placeholder art is expected and is no finding.

## The line

The session writes the line only after the owner's words in chat or on the issue, quoting them; it never writes it for the owner. One line in the FEAT's `## History`, dated the day of the play:

```markdown
- 2026-11-20 playtest: 0.3 greybox at 1a2b3c4 — go — owner: "fluid and fun, go on"
```

Fields: the date, `playtest:`, the block's heading name, the closure commit, the outcome (`go`, `retune` or `rule`) and the owner's words. The closure record (`closure-record.md`) gets a `Playtest` row that cites the line. A repeat play adds a new line; an old line is never edited.

## Outcomes

| Outcome | Then |
|---|---|
| `go` | `validate` the greybox block. `check_spec.py` (KIT-096) accepts a polish block only once every earlier block is delivered: under `release: merge` `validate` delivers the greybox block at once; under `release: manual` it stays `validated` until `sdd-release` delivers it, whose § 4 acceptance is this line (no second playtest, no captures), and only then is the polish block added, written and cut (skill `sdd-tasks` § 1) |
| `retune` | new values inside each tunable's range need no spec change: a task row in the greybox block names the REQ and the values (a defect of its feel, with its History line), and the owner plays again once it merges |
| `rule` | a rule or a range is wrong: `sdd-clarify` amends the REQ, and the block does not validate until a later play says `go`, or the owner cancels it |

## Checks

- `sdd-check` C16 reads the line: a polish block written or cut with no `go` line for its greybox block is a high finding.
- No script checks the line: `check_spec.py` checks only the History lines of `validate` and `deliver`. A script rule waits for the first projects that use passes.
