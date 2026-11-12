---
name: sdd-to-card
description: SDD step 8 — one GitHub issue per task row plus the FEAT card. Use when cutting issues or closing a FEAT. Not for PR operations (skill git).
argument-hint: "FEAT-nnn [--project <number>]"
triggers:
  - user
disable-model-invocation: true
allowed-tools:
  - read
  - edit
  - exec
---

# SDD 8 — To Card

Process: `../sdd-constitution/references/sdd-process.md`. This step changes GitHub state; run it only on user invocation and never print a token.

## 1. Cut one issue per task row

- Title: `[FEAT-nnn Tn] <first ~8 words of the Task cell>`.
- Body: the project's `.github/ISSUE_TEMPLATE/task.md` (kit source `platforms/kits/github/ISSUE_TEMPLATE/task.md`) filled verbatim from the row — no rewriting, no added scope. Field map and states: `references/task-issue.md`.
- `Spec` is the FEAT path derived from the title; `DoD` is the proof plus the gate commands of `<Repository>/AGENTS.md` § Commands. Both are filled mechanically.
- Issues are cut in wave order, in the single backlog repository the project names; the target repo goes in `Repository`.
- A FEAT card (`FEAT-nnn: <title>`) is optional and mirrors status as today — labels/Project status follow FEAT status; a non-null `flag` adds `flag`.
- `card` stores only the optional FEAT card number; task issue numbers are never written to the FEAT — its state derives from GitHub.

## 2. Create or update

Create the task issues with `gh issue create`; a fresh cut carries `status:proposed` until the architect approves it. When the optional FEAT card is wanted: if `card: null`, create it with `gh issue create`, write its number to frontmatter and commit that link; otherwise use `gh issue edit` to update title/body/status labels.

Create missing `feature`/`status:*` labels when authorized. Add to a requested/configured Project and update its Status field; ask before creating a Project.

## 3. Close delivery

A task issue closes through its PR, whose last line is `Closes <owner>/<docs-repo>#N` — cross-repo when the code lives elsewhere. The FEAT card closes when every task issue is closed; close it with the delivered PR references. Do not create separate cards for REQ/DEC/DEBT unless the user explicitly requests a debt issue.

## 4. Verify

Run `gh issue view <n>` and confirm title, status, links and the FEAT `card` agree.

Done when: one issue per task row is cut verbatim in wave order, FEAT `card` and statuses agree with GitHub, the frontmatter change is committed, and no specification body was duplicated.
