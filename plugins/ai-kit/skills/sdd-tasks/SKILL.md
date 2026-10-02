---
name: sdd-tasks
description: SDD step 6 — dependency-ordered implementation tasks. Use when a FEAT has an approved technical plan. Not for execution (skill sdd-implement).
argument-hint: "FEAT-nnn"
triggers:
  - user
disable-model-invocation: true
allowed-tools:
  - read
  - edit
---

# SDD 6 — Tasks

Process: `../sdd-constitution/references/sdd-process.md`.

## 1. Confirm the plan

Require `status: planned` and a Plan section with files, boundaries and test strategy.

## 2. Split by verifiable outcome

- Each task takes roughly 5–30 minutes, touches at most five named files and has one command/test proving completion.
- Split any title needing “and also”. Tests travel with behavior, not in an end-of-feature test task.
- Order contract/types → domain/tests → persistence/migration → adapters/integration → client → flag/docs.
- For a business rule, the first implementation task writes the failing domain test.

## 3. Write task rows

Each row contains `T-nn`, imperative title, exact files, proof, covered acceptance criteria, dependencies and state. Mark dependency-independent rows `[P]`.

```markdown
| ID | Task | Files | Proof | Covers | Depends on | State |
|---|---|---|---|---|---|---|
| T-01 | Define MoveRequest contract | protocol/... | example validates | CA-1 | — | todo |
```

States: `todo`, `doing`, `done`, `blocked`.

## 4. Check coverage

Every acceptance criterion appears in at least one task; every task covers a criterion or is explicitly infrastructure. Run `sdd-analyze` A8 and remove vague “implement the rest” rows.

Done when: tasks are dependency ordered, independently provable, mapped both ways to criteria and ready for one-at-a-time execution.
