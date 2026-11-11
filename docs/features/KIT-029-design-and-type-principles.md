---
id: KIT-029
title: "Code and architecture rules name one owner per decision, a valid data shape, idempotent steps and no silenced warning"
status: confirmed
confirmed: "2026-11-10 (owner, ub-mode evaluation decisions D1–D8 in the chat of the ub-mode evaluation session; implementation prompt launched 2026-11-11)"
issue: "#131"
pr: ""
---

# KIT-029 — Code and architecture rules name one owner per decision, a valid data shape, idempotent steps and no silenced warning

## Problem and evidence

The owner evaluated the ub-mode principles against the kit on 2026-11-10
(`/Users/christian/Developer/GitHub/PROPOSAL-UB-MODE-2026-11-10.md` § 3, rows 1, 3, 4, 5, 8, 10, 13–20 and 27) and
decided to merge the adopted ones into existing skills and rules (D1), with compiler suppression allowed only on the
narrowest scope with a reason (D4). Facts re-checked at kit `49b2137`:

- [FACT] `plugins/dev-core/skills/code-standards/SKILL.md:23` reads the glossary but never adds to it: "consult the
  project glossary before introducing a synonym."
- [FACT] `plugins/dev-core/skills/code-standards/SKILL.md:60` subtracts only dead code: "Delete dead code before adding
  another abstraction."
- [FACT] `plugins/architect-core/skills/architecture/SKILL.md:22` validates but does not parse: "Validate external
  input at the adapter boundary, then trust the typed interior."
- [FACT] `git grep -i -E 'illegal state|pure function|SuppressWarnings|warning_ignore|bolt' 49b2137 -- plugins` prints
  nothing; "one place" appears only in `plugins/extras` (frontend design); `architecture/SKILL.md` never says
  "idempotent".
- [FACT] `plugins/dev-java/rules/java.md` and `plugins/dev-godot/rules/godot.md` hold 11 bullets each and no line on
  warning suppression.
- [FACT] stratics-server at `5bce89c2` holds 55 `@SuppressWarnings` in 31 files (38 `unchecked`, 17 `unused`);
  stratics-client at `f98e0091` holds 45 `@warning_ignore` lines in 7 files outside `addons/` (read-only `grep`).
- [FACT] stratics-client `app/network/network.gd` at `f98e0091`: `_validate_message` starts at line 619 and the next
  function at line 1052, a 433-line `match` whose arms hold inline checks.

## Change

`plugins/dev-core/skills/code-standards/SKILL.md` (64 → 73 lines):

- § 2, line 23: "- Use one English term per concept; consult the project glossary before introducing a synonym, and add
  a new domain term to the glossary in the same change."
- § 3 gains: "- A `match`/`switch` whose arms each make one call is fine; arms that hold logic are split into functions
  or become a table."
- § 7, line 60 becomes: "- Fewer files win when cohesion remains high. Remove what the change makes unnecessary (dead
  code, flag, special case, layer) before adding another abstraction."
- § 7 gains: "- Leave clear, local code alone: no drive-by refactor outside the flow the change touches."
- New § 8 "Design the change before the edit":
  - "- One decision (rule, threshold, mapping) lives in one place; every other site reads it from there."
  - "- Get the data shape right before the logic: a shape that holds only valid states removes the branches that would
    repair it."
  - "- A new requirement is not bolted onto the old design: build the smallest edit of the design you would have made
    had the requirement been there from the start, and deliver it in pieces."
  - "- When work is not obvious at a glance, do one unit by hand, then make a tool reproduce it (the hand-done unit is
    the tool's test); do first what helps every later step."
- "Done when" ends "…any deliberate ceiling records its evolution trigger, and each decision lives in one place."

`plugins/architect-core/skills/architecture/SKILL.md` (56 → 62 lines):

- § 1 appends: "Business logic is a pure function: I/O, clock and randomness are passed in."
- § 2, line 22 becomes: "- Parse external input once at the adapter boundary into a typed value, then trust the typed
  interior; never re-validate it inside."
- § 2 gains: "- Model the domain so illegal states cannot be built: Java `sealed` types and `record`s with validating
  constructors, enums over strings; GDScript enums and typed classes over a raw `Dictionary` or `String`."
- New § 8 "Make state changes safe to repeat":
  - "- Every command, script, migration and loop step is idempotent and crash-safe: run twice, or again after a crash
    half-way, it leaves the same state."
  - "- State that two actors would write gets one writer, enforced by the structure (an owner object or a queue), or
    each actor gets its own copy."
- "Done when" ends "…no speculative architecture added, illegal states cannot be built, and every state change is
  idempotent with one writer."

`plugins/dev-java/rules/java.md` (11 → 12 bullets) gains: "- Never: `@SuppressWarnings` to hide a warning; `unused`
means delete the code, and `unchecked` sits only on the narrowest declaration with a comment naming why the type cannot
be expressed."

`plugins/dev-godot/rules/godot.md` (11 → 12 bullets) gains: "- Never: `@warning_ignore` to hide an untyped or unused
warning (type it or delete the code); any other sits on the narrowest line with a comment naming why."

Skill descriptions do not change, so the plugin `INDEX.md` files stay identical. New eval cases, none naming the skill:

- `plugins/dev-core/evals/code-standards-one-decision-one-place` (one owner for a duplicated evolve level)
- `plugins/dev-core/evals/code-standards-match-one-call-arms` (a one-call `match` stays as it is)
- `plugins/dev-core/evals/code-standards-no-bolt-on-flag` (a third mode reshapes the design instead of a third flag)
- `plugins/architect-core/evals/architecture-illegal-states` (a string status and nullable fields become types)
- `plugins/architect-core/evals/architecture-idempotent-import` (an import that deletes its input first)
- `plugins/architect-core/evals/architecture-pure-battle-core` (damage that reads `randf` and the clock)

No eval exercises the two suppression bullets: [FACT] rule files reach Claude only through `sync-project.sh`, which
copies them into the project's `.claude/rules/` (`platforms/tools/sync-project.sh:8`), and a plugin eval loads the
plugin, not a synced project, so a case could only grade the base model.

## Proof

Run from the worktree root at the PR head:

<!-- proof lines are filled after the gates run -->

## History

- 2026-11-10: confirmed (owner, ub-mode evaluation decisions D1 and D4).
- 2026-11-11: implementation prompt launched; issue #131.
