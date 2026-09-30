---
name: sdd-tasks
version: "1.0"
description: SDD step 6 — breaks a FEAT's plan into small tasks ordered by dependency, each with a verifiable completion criterion and an associated test. Use after plan; the output is the Tasks section in the FEAT.
argument-hint: "FEAT-nnn"
triggers:
  - user
allowed-tools:
  - read
  - edit
---

# SDD 6 — Tasks

Prerequisite: `status: planejada`.

## Splitting rules

- A task is **small**: ≈ 5-30 min of execution, ≤ 5 files, a single command/test that proves completion. If the description needs "and also", they are two tasks. Each task names the exact paths (not "the module's files").
- Order: contract/types → domain + unit tests → persistence + migration → adapters + integration → client → flag/docs. Tests travel **with** the task, not as a separate task at the end.
- Each task: `T-nn` · imperative title · planned files · completion criterion (command or test that proves it) · acceptance criteria covered (`CA-n`) · dependencies (`T-mm`).
- Independent tasks marked `[P]` (parallelizable).
- First task of every FEAT with a business rule: "write failing domain tests" (Red).

## Format (the FEAT's **Tasks** section)

```markdown
| ID | Task | Files | Proof of completion | Covers | Depends on | State |
|---|---|---|---|---|---|---|
| T-01 | Define MoveRequest/MoveResult messages in the contract | protocol/... | example validates against the schema | CA-1, CA-2 | — | todo |
| T-02 [P] | Movement domain tests (failing) | server/domain/src/test/... | `./mvnw -pl domain test` red for the right reason | CA-1..3 | T-01 | todo |
```

States: `todo · doing · done · blocked`.

## Completion criteria

- Every acceptance criterion appears in ≥1 task; every task covers ≥1 criterion (or is explicit infra).
- No "implement the rest" task.
- `sdd-analyze` A8 passes.
