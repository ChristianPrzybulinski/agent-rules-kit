---
id: FEAT-000
title: "[Short infinitive title: Authenticate player]"
status: proposed
requirements: []
processes: []
depends_on: []
scope: []
milestone: null
evidence: []
flag: null
issue: ""
owner: "[product]"
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
---
<!-- Created by sdd-plan from a refined NEED, or from the request itself under sdd.needs: false: a FEAT is one use case,
     one actor and one goal, for the project's life, never a bucket. `processes` names the process steps it realizes
     (PROC-nnn, PROC-nnn S<a>–S<b>, PROC-nnn S<n> or PROC-nnn A<n>; one process holds the use cases of N FEATs) and
     `enablers` the ENBs it changes; a version block that serves another step, cites a REQ only other steps cite or
     names another ENB fails spec_trace.py check (the anti-bucket rule).
     ## Versions holds one block per project version (release.versioning: semver → `### 0.3.0`, milestone → `### M5`;
     a greybox and its polish are two blocks, `### 0.3 greybox` and `### 0.3 polish`). Each block holds its Status,
     its Scope delta, its Plan delta, its task rows and its Closure; only the last block is open, every earlier one is
     delivered or cancelled, and the FEAT's `status` is the last block's. A block above sdd.max_feat_tasks rows fails
     check_spec.py: the rest goes to the next block. Once a block reaches planned, a new or amended REQ goes to the next
     block, and a row is added only for a defect or a missing step of a REQ in its Scope, with a History line that
     says which (sdd-check C17). Task row ids continue across blocks and are never reused.
     status: proposed while sdd-plan drafts it, planned after a clean full-scope sdd-check; in-progress is derived once a
     task row of the last block is doing or done (with a canonical issue, row states carry execution/merge evidence;
     legacy task issues and tracker: none TASK files retain derived states), and status --write records that move in History whichever row moved it, in the frontmatter and
     the block's Status line;
     validated is written by sdd-review and delivered by sdd-release (or sdd-review under release: merge), through
     spec_trace.py with their History line; clarified remains only on FEATs written before the NEED flow. Never
     edit status by hand.
     Register (skills/sdd-constitution/references/sdd-process.md, Register): technical documentation: Plan, contracts,
     data, assets and tasks, with links to the functional layer; it cites a REQ and never restates its rule. -->

# FEAT-000 — [Title]

## Problem / value

[One line, then the NEED it delivers: `NEED-nnn`. The full problem, Situations and scope live in the NEED.]

## Scope

- Use case: [the actor] [the goal], one actor and one goal.
- [the REQs this use case implements across its versions, new or amended: `REQ-F-nnn`]

## Out of scope

- [REQs or parts left to another FEAT, and which]

## Acceptance criteria
<!-- Technical: what the delivery's tests prove (contract, unit, integration, e2e). The functional criteria are the REQs'
     Verification; each row cites the REQ ids it proves, and every REQ in Scope is proved by at least one row. -->

| ID | Given | When | Then | Test type | Proves |
|---|---|---|---|---|---|
| CA-1 | [initial state] | [action] | [observable result] | unit / integration / contract / e2e | REQ-F-000 |
| CA-2 | [sad path: invalid input / no permission / timeout] | | | | REQ-F-000 |

## Linked requirements

- `REQ-F-000` — [title]
- `REQ-NF-000` — [title]

## Relations

- Depends on: [FEAT-xxx or —]
- Conflicts/overlaps: [—]
- Related legacy: [path in the archive, if any — `[FACT]` only if verified]
- Evidence: [frontmatter `evidence` IDs → `docs/legacy/evidence.md#e01`]

## Open questions

- [NEEDS CLARIFICATION: ...]

## Plan
<!-- filled by sdd-plan: one ### section per name in spec.md sdd.plan_sections, in this order (Risks and Tests always);
     each holds its content or one line "— <why it does not apply>". Task cells point to "Plan § <section>". It is the
     use case's current design: a version block's Plan delta says which sections that version changed. -->

### Design
<!-- cites each process state the FEAT implements (PROC-nnn and the state) and what holds it. With docs/spec/enablers/,
     it ends with the walk table | Step | REQ | ENB contract | Task |: each step or REQ to the ENB contract that
     carries it, Task filled by sdd-tasks (skill sdd-plan § 4; sdd-check C18). -->

### Contract
<!-- with docs/spec/enablers/: cite each contract as its catalog row ENB-nnn:<contract> and list those ENBs in the
     frontmatter `enablers`; state only the change (sdd-check C19). -->

### Data
<!-- one line per tunable of the FEAT's REQs (Tunable not `fixed`): REQ and value, range and unit, and its exposure
     (content key, config entry or debug control); sdd-check C14. -->

### UI

### Assets
<!-- only when sdd.plan_sections lists Assets (off by default): one row per asset the delivery needs before the cut;
     Kind with its frame count or duration, Source made / licensed / legacy with its path or URL, License, Serves a
     REQ id or the REQ mock it matches. -->

| Asset | Kind | Source | License | Serves |
|---|---|---|---|---|

### Flag

### Tests

### Observability

### Risks

### Dependencies

## Versions
<!-- one ### block per project version, oldest first; a released block is frozen history and may fold to its Status,
     Scope and Closure lines plus the release tag. -->

### [0.1.0, or M1 under release.versioning: milestone]

Status: proposed
Scope: [what this version adds or changes, on one line: REQ-F-000 (new) · REQ-F-001 (amended) · ENB-000:<contract>]

#### Plan delta

- [the Plan sections this version changes, or "— first version: the whole Plan"]

#### Tasks
<!-- filled by sdd-tasks in a spec PR, tracked once approved or merged. All GitHub Item cells name the same FEAT issue.
     Status is recorded per row with evidence, mark-done for completion; the shared issue never overwrites it.
     Legacy task issues and tracker: none TASK files retain derived states. Item is — until tracking is linked.
     A set of items that share one form (species references, move handlers, quests) is one row, or one per group sharing a
     contract, never one per item (skill sdd-tasks § 2). -->

| ID | Task | Files | Proof of completion | Covers | Depends on | Status | Complexity | Model | Wave | Item |
|---|---|---|---|---|---|---|---|---|---|---|

#### Closure
<!-- written by sdd-review on main after the block's last row merges, before spec_trace.py validate: Main commit, rows
     for the task proofs, the lint, the broad suite, each REQ-NF measurement and the missing-test rows filed, outcome,
     retro -->

## Decisions
<!-- one line per choice the spec did not fix, written when its task closes: YYYY-MM-DD T<n> (<PR>): chose X over Y because Z. New [DECISION] lines of this spec go here; Open questions keeps only open questions. The action log stays in the PR body. -->

## Audit
<!-- filled by the calling session from the sdd-check report (or a FEAT-000.checklist.md file) -->

## History

- YYYY-MM-DD plan: created from NEED-nnn.
