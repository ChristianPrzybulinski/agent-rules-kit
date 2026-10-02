---
name: sdd-implement
description: SDD step 7 — task-by-task Red-Green-Refactor delivery. Use when a FEAT has ordered tasks. Not for completion verdicts (skill validate-implementation).
argument-hint: "FEAT-nnn [T-nn]"
triggers:
  - user
allowed-tools:
  - read
  - glob
  - grep
  - edit
  - exec
---

# SDD 7 — Implement

Process: `../sdd-constitution/references/sdd-process.md`.

## 1. Start the delivery branch

Create or use `feature/FEAT-nnn-slug` from updated `main`; set `status: in-progress`. Work one task at a time unless independent `[P]` tasks have disjoint files.

## 2. Execute each task

1. Mark `doing` and read every named file.
2. For behavior, run/write the test first; it must fail for the intended reason.
3. Implement the minimum, make the test green, then refactor.
4. Run the task's proof literally and summarize output in History.
5. Review conformance to task/criterion before code quality; a scope finding returns to implementation.
6. Commit atomically as `feat(scope): <task>` with `Refs: FEAT-nnn`; mark `done`.

A dependency/product/rule blocker becomes `blocked` with reason; never invent a workaround. Move only to an independent task.

## 3. Close the implementation

Use `../update-docs/references/living-docs.md`, update CHANGELOG/README/API docs and run full repository gates. Then call `validate-implementation`; PARTIAL/NOT READY returns to the missing task.

Incomplete work may merge only behind a recorded flag that defaults off. A flag continuously on for more than 30 days creates a `DEBT-nnn` removal item. Security/integrity rules never hide behind a flag.

## 4. Open the PR

After READY and green gates, open a squash PR with criteria/proofs and `Refs: FEAT-nnn`. Set `validated` after the green PR and `delivered` after merge.

Done when: all tasks and proofs are recorded, full gates pass, validation is READY, and incomplete merged behavior is safely flagged with expiry handling.
