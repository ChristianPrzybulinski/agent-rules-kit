---
id: KIT-094
title: "Greybox and polish passes, as two version blocks of one FEAT, with an owner playtest gate"
status: in-progress
confirmed: "2026-11-16 (owner, kit chat: \"Sim, faça\" on E § 17, backlog G5; \"Yes, blocks\" on E § 17.1)"
issue: "#335"
pr: ""
---

# KIT-094 — Greybox and polish passes, as two version blocks of one FEAT, with an owner playtest gate

## Problem and evidence

[FACT] The owner's game-profile evaluation (`KIT-GAME-PROFILE-EVALUATION-2026-11-16.md` in the owner's workspace, "E"
below) § 4: a new game mechanic needs merged greybox code accepted by a playtest before its polish is cut. The spike
throws its code away, and release acceptance (`sdd-release` § 4, "a playtest for a game" in prose with no key behind
it) comes after both passes. KIT-088 added the profile keys `sdd.passes` (`[]`, or `[greybox, polish]` in the `game`
preset) and `sdd.acceptance` (`captures` or `playtest`), and no skill or tool read them. § 9.2 item 1: a greybox of
coloured rectangles has no mock, so `visual_approval` (skill `review`) and row rule j (`row_checks.py`) would hold
its rows for nothing.

Owner decisions (E § 17.6): the owner alone signs the greybox playtest; the name is "passes"; greybox and polish are
two version blocks of one FEAT (§ 17.1, "Yes, blocks"), which replaces the two-FEAT split of the issue's first text.

## Change

- `sdd-plan` § 3: under `sdd.passes`, a NEED that adds a new mechanic (never a content route) is planned as two version
  blocks of one FEAT, `### <version> greybox` then `### <version> polish`. The greybox block holds rules, Design,
  Contract and Data tunables with placeholder art, no Assets row and no feel value; the polish block owns § Assets and
  the feel values inside each tunable's range, amends no rule, and waits for the playtest line.
- `sdd-tasks` § 1: a polish block's rows are written and cut only after the greybox block's playtest line with outcome
  `go`; a greybox block's rows need no `evidence:` clause.
- `sdd-review`: new reference `references/playtest.md` (when, who: the owner alone, the dated History line
  `- <date> playtest: <block> at <sha> — go | retune | rule — owner: "<words>"`, and what each outcome does); § 3 asks
  for it before `validate` on a greybox block.
- `sdd-release` § 4 reads `sdd.acceptance` (`captures` or `playtest`) instead of the prose branch "a playtest for a game";
  a greybox block's acceptance is its playtest line.
- `review` § 2 and `row_checks.py` rule j: a row of a greybox block is exempt from `visual_approval` and from rule j while
  `sdd.passes` lists greybox. Code: new functions `pass_rows`, `mark_passes`, `greybox_exempt`, a `Row.pass_name`
  field, and one-line call sites in `parse_rows` and `rule_j`.
- `sdd-check` row C16 (full scope, high): a greybox block with Assets rows or a feel value; a polish block that amends a
  rule its greybox block delivered; a polish block with no greybox block of its version before it, or written or cut
  before that block's `go` line.
- `row-checks.md` rule j and the `passes` description in `profile.schema.json` name the exemption.

Choices:
- Version blocks are the only shape. The two-FEAT form (a polish FEAT that `depends_on` its greybox FEAT) is dropped:
  the owner chose blocks, E § 17.1 has C23 forbid two FEATs with one actor and goal, and supporting both would need a FEAT-level
  pass marker (a schema change) for a form no project uses.
- KIT-096's block reader (`check_spec.version_blocks`) is not on `main`, so `row_checks.py` carries `pass_rows`, a
  minimal reader of the `### <version> <pass>` headings, kept apart so that reader can replace it. On `main`,
  `parse_rows` reads only a `## Tasks` table, so the exemption reaches rows once the KIT-096 task-table helper makes
  `parse_rows` read block tables; `mark_passes` maps by task id, which KIT-096 keeps unique per FEAT.
- C16 is a judgment row, not a script rule, and no script checks the playtest line (`playtest.md` § Checks).
- `passes: []`, the default, changes nothing: no block is exempt, and the skills' new text applies only under the key.
  Not a project.kind fork: every skill reads `sdd.passes` and `sdd.acceptance`, never `project.kind`.

## Proof

- Red first: `test_row_checks_passes.py` (10 tests) failed 7 before the change (1 assertion: rule j warned on a
  greybox row; 6 on the missing `pass_rows`/`mark_passes`), green after under `python3.12` and `/usr/bin/python3`.
- Byte for byte: `row_checks.py check --all --all-rows` and `check_spec.py` on `platforms/ci/fixtures/consumer` and
  on a copy of Stratics' `docs/spec`, under both Pythons, before and after: 8 outputs, no difference.
- `bash platforms/tools/check.sh`, `bash platforms/tools/check.sh --links`,
  `python3.12 platforms/tools/run_tests.py --layer unit,contract`, `--layer integration --changed-from origin/main`.

## History

- 2026-11-16: confirmed (owner, E § 17, backlog G5).
- 2026-11-17: implemented on `feat/kit-094-passes`; PR pending.
