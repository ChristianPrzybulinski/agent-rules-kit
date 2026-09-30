---
name: sdd-implement
version: "1.0"
description: SDD step 7 — executes a FEAT's tasks one by one (Red→Green→Refactor), on branch feature/FEAT-nnn, updating task states, docs and CHANGELOG; stops on a blocker and invents nothing. Use after tasks.
argument-hint: "FEAT-nnn [T-nn]"
triggers:
  - user
allowed-tools:
  - read
  - glob
  - grep
  - edit
  - write
  - exec
---

# SDD 7 — Implement

Prerequisite: the *Tasks* section exists. Kit rules and the repo's `AGENTS.md` apply in full.

## Steps

1. Branch: `git switch -c feature/FEAT-nnn-slug` from an updated `main` (if it does not exist yet). `status: em-implementação`.
2. For each task in order (or the indicated `T-nn`):
   1. Mark `doing`. Read the real files it will touch.
   2. Test first when there is behavior: write/run → must fail for the right reason. Didn't fail? The task was not understood — stop and review.
   3. Implement the minimum to go green. Refactor with green tests.
   4. Run the task's *proof of completion* literally; paste the summarized output into *History*.
   5. **Two-stage review**, in this order and unmixed: (a) *conformance* — does the diff do exactly what the task/CA asks, nothing more, nothing less? (b) only if (a) passed: *quality* — simplicity (`agents/rules/development/simplicity.md`), names, tests, security. A finding in (a) goes back to step 3 before any polishing.
   6. Atomic commit: `feat(scope): <task>` + `Refs: FEAT-nnn`.
   7. Mark `done`.
3. Blocker (missing dependency, product decision, violated rule) → `blocked` + reason in the FEAT; do **not** work around it. Move to an independent `[P]` task if any; otherwise report.
4. When all are done: checklist from `agents/rules/documentation/living-docs.md` (CHANGELOG `Unreleased`, README, Javadoc/docstring, flag recorded). Run the full gates (`./mvnw spotless:check verify`, `godot --headless --quit`, etc.).
5. Call `core/validate-implementation FEAT-nnn`. PARTIAL/NOT READY → back to step 2 with the missing tasks.
6. READY → `gh pr create` (Conventional Commit title; body with criteria ✓, commands run, `Refs: FEAT-nnn`). Status changes to `validada` only after the PR is open with green gates; `entregue` after merge.

## Do not

- Implement outside the FEAT's scope ("while I'm here"). Note it as a follow-up.
- Disable a test, lower a coverage gate, suppress a CVE without justification.
- Claim it was tested without a recorded command output.
