---
id: KIT-030
title: "Tests must fail on empty returns, surviving mutants on changed lines are handled, and both languages get the same checks"
status: confirmed
confirmed: "2026-11-10 (owner, ub-mode evaluation decisions D1 and D5 in the chat of the ub-mode evaluation session; implementation prompt launched 2026-11-11)"
issue: "#132"
pr: ""
---

# KIT-030 — Tests must fail on empty returns, surviving mutants on changed lines are handled, and both languages get the same checks

## Problem and evidence

The owner evaluated the ub-mode test rules against the kit on 2026-11-10
(`/Users/christian/Developer/GitHub/PROPOSAL-UB-MODE-2026-11-10.md` § 3, rows 7, 24, 25 and 29) and set the parity
rule D5: every quality check one language has, the other gets with the same rule, built by the kit when no tool
exists, advisory until its false-positive rate is measured. Facts re-checked at kit `49b2137`:

- [FACT] `plugins/dev-core/skills/testing/SKILL.md:23` closes the GDScript gap with "no line, branch or mutation
  percentage gate; the tooling does not exist", and names no substitute check.
- [FACT] `plugins/dev-core/skills/testing/SKILL.md:46` (§ 5) says what to assert, not how to call the code: "Assert the
  externally observable result or state transition."
- [FACT] `plugins/dev-core/skills/testing/SKILL.md:19` keeps mutation score ≥80% as the only mutation rule, so a
  surviving mutant on a changed line passes while the score stays above 80%.
- [FACT] `git grep -i -E 'surviv|equivalent mutant|returned null|manual proof|parity|public entry' 49b2137 -- plugins`
  finds only an `sdd-tasks` eval description about labelling a manual proof and the `twelve-factor` dev/prod parity
  heading; no test rule covers empty returns, survivors, impractical tests or language parity.
- [FACT] The proposal's parity table (§ 4, lines 122–130) lists GDScript coverage and mutation as missing in
  stratics-client: gdUnit4 has neither, while stratics-server gates JaCoCo 1.00 and PIT 80 %.

## Change

`plugins/dev-core/skills/testing/SKILL.md` (60 → 68 lines):

- § 1 gains: "Every surviving mutant on a changed line is killed by a new assertion, deleted as dead code, or named as
  equivalent in the PR body; a green 80% gate does not excuse it."
- § 1, the GDScript paragraph (line 23) opens: "GDScript (Godot): no line, branch or mutation percentage gate yet; the
  kit is building the tools (KIT-034 coverage, KIT-035 mutation), and until they gate, the § 5 empty-return check
  stands in for them. Every game rule …" (the rest of the paragraph is unchanged).
- § 1 gains: "Parity: every quality check one language has (coverage, mutation, complexity, duplication), the other
  gets with the same rule; when no tool exists the kit builds one, and each tool stays advisory until its
  false-positive rate is measured."
- § 5 gains three bullets:
  - "- Call the code through the public entry its user uses (public method, port, message or scene contract) and
    assert what that user sees; never reach into a private helper."
  - "- A test that would still pass if every function under test returned null, zero or empty proves nothing: rewrite
    it with the expected value, or delete it."
  - "- When an honest test is impractical, write none: record the manual proof (the command or steps and what was
    observed) in the PR body instead."
- "Done when" ends "…no test sleeps or asserts implementation calls, no test passes on empty returns, and every
  surviving mutant on a changed line is killed, deleted or named."

`plugins/dev-godot/skills/godot-standards/SKILL.md` (55 → 56 lines), § 5 gains after the test-runner line: "A test
that would still pass if every function under test returned null, zero or empty is rewritten or deleted (skill
`testing`, section 5); until GDScript coverage and mutation gate, that check stands in for them."

The 80 % PIT threshold and the 100 % domain coverage gates do not change. Skill descriptions do not change, so the
skill rows of the plugin `INDEX.md` files stay identical; each new eval case gains its line under `## evals/` there,
because `check_kit.py` fails on an unlisted case (`platforms/ci/validations/check_kit.py:974`–`991`). New eval
cases, none naming the skill:

- `plugins/dev-core/evals/testing-empty-return-passes` (a JUnit `assertTrue(total >= 0)`)
- `plugins/dev-core/evals/testing-surviving-mutant-green-gate` (a boundary mutant survives at 86 %)
- `plugins/dev-core/evals/testing-honest-test-impractical` (an audio crossfade judged by ear)
- `plugins/dev-core/evals/testing-parity-gdscript-coverage` (a proposed permanent GDScript exemption)
- `plugins/dev-godot/evals/godot-standards-empty-return-test` (a gdUnit4 test of a private helper with `>= 0.0`)

## Proof

Run from the worktree root at the PR head:

<!-- proof lines are filled after the gates run -->

## History

- 2026-11-10: confirmed (owner, ub-mode evaluation decisions D1 and D5).
- 2026-11-11: implementation prompt launched; issue #132.
