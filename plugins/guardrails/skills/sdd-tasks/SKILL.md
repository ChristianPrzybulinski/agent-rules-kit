---
name: sdd-tasks
description: SDD step 5 — dependency-ordered implementation tasks. Use when a FEAT has an approved technical plan. Not for execution (skill sdd-implement).
argument-hint: "FEAT-nnn"
triggers:
  - user
disable-model-invocation: true
allowed-tools:
  - read
  - edit
---

# SDD 5 — Tasks

Process: `../sdd-constitution/references/sdd-process.md`.

## 1. Confirm the plan

Require `status: planned` and a Plan section with files, boundaries and test strategy.

## 2. Split by verifiable outcome

- Each task is a thin slice one fresh agent context can finish: roughly 5–30 minutes, at most five named files and one command/test proving completion. A mechanical change across the codebase (rename, retype) is one task, and a spec value a row needs (version, name, limit) is copied into it verbatim.
- Split any title needing “and also”. Tests travel with behavior, not in an end-of-feature test task.
- Order contract/types → domain/tests → persistence/migration → adapters/integration → client → flag/docs.
- For a business rule, the first implementation task writes the failing domain test.

## 3. Write task rows

Each row contains `T-nn`, imperative title, exact rooted files (tests included), proof, covered criteria, dependencies, state, and the three cut fields `Complexity` (Low|Med|High), `Model` (tier, see `references/waves-and-models.md`) and `Wave`. Mark dependency-independent rows `[P]`.

```markdown
| ID | Task | Files | Proof of completion | Covers | Depends on | State | Complexity | Model | Wave |
|---|---|---|---|---|---|---|---|---|---|
| T-01 | Define MoveRequest contract | protocol/... , tests/... | example validates | CA-1 | — | todo | Low | small | 0 |
```

States: `todo`, `doing`, `done`, `blocked`.
Waves: `references/waves-and-models.md` (wave 0, shared files, cross-FEAT order); wave numbers are FEAT-local and a cross-FEAT dependency points to a task cut earlier.

## 4. Check coverage

Every acceptance criterion appears in at least one task; every task covers a criterion or is explicitly infrastructure. Run `sdd-check` row C8 (criterion without task or task without criterion) and remove vague “implement the rest” rows.

## 5. Pre-cut checklist (before issues are created)

Check every row. A row that fails one of these items is fixed before its issue is cut:
- **Tests in scope.** `Files` includes the test paths for any new code. A row that adds code without a test path is incomplete.
- **Cross-feature fields.** Every field the task reads from or writes to another feature's contract (message, schema, table) exists in that feature's artifact. Fix the contract first, never inside the implementing PR.
- **Executable proof.** Every proof line runs unattended in CI or the review gates, as a deterministic command. A manual check (UI, mail capture) is labelled as such and paired with an automated one.
- **Neighbour files.** If the work needs a file outside the row's `Files` (a config key, a shared CI workflow), that file joins the cell, or the row names the task that owns it.
- **Generated and build files.** `*.import`, `*.uid`, `*.translation`, `pom.xml`, `application.yml` or the project's equivalents join `Files`.
- **Value domains.** Every contract field or table column names its value domain and the public identifier of any entity it names.
- **Proof wording.** A proof line contains none of the words the project's gates refuse (the issue's `Notes` field, filled by `sdd-to-card`, names the project's allowlist location; never hard-code it here).

The architect reviews every PR of these tasks against FEAT/REQ/DEC; an executor's "done" report is not evidence, the diff and the re-run proofs are.

## 6. Write the progress file

Create `docs/spec/progress/FEAT-nnn.json` from the table: one entry per row with `id`, `title` (the Task cell up to its first `: ` or `. `, max 200 chars), `files` (the Files cell as a list, backticks removed), `proof` (the Proof cell), `passes: false`, `notes: ""`, and `issue` when the task issue already exists; `generated` is today. Schema: `platforms/ci/schemas/progress.schema.json`; example: `platforms/kits/sdd/progress.example.json`. Validate with `check.sh --spec docs/spec` (kit) or `.github/spec-lint/check_spec.py docs/spec .github/spec-lint/schemas` (project). Commit it with the task table.

Done when: tasks are dependency ordered, independently provable, mapped both ways to criteria, pass the pre-cut checklist, are ready for one-at-a-time execution and the progress file validates.
