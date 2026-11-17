---
name: sdd-plan
description: "SDD step 4 — one FEAT per delivery of a refined NEED: its Plan sections and decisions. Use when a NEED is refined. Not for task rows (skill sdd-tasks)."
argument-hint: "NEED-nnn [technical constraints]"
triggers:
  - user
disable-model-invocation: true
allowed-tools:
  - read
  - glob
  - grep
  - edit
  - exec
---

# SDD 4 — Plan

The technical refinement: cuts a refined NEED into deliveries, creates one FEAT per delivery and plans it. Process: `../sdd-constitution/references/sdd-process.md`. Template: `../../templates/spec-feature.md`. It resolves the project profile first (`../session/references/project-profile.md`) and reads `spec_root` and the `sdd` parameters `plan_sections`, `max_feat_tasks` (`../sdd-constitution/references/sdd-parameters.md`), `passes` and `decision_folding`.

With `sdd.flow: feat-only` (the `tooling` preset, KIT-100) there is no NEED and no REQ: under `sdd.record_when: big-change` a change gets a FEAT only when it is big by the project's own threshold (its contributing guide), and any other change needs only its changelog line and its PR body's why. The FEAT comes from `../../templates/spec-feature-lite.md` with the next `<sdd.id_prefix.feature>-nnn` id; Problem and evidence holds the request, the acceptance criteria hold the rules with their `Proof` commands, and its `issue` names the one item. § 1 reads the request, § 2 and the REQ bullets of § 3 do not apply, `sdd-tasks` writes no rows (`task_table: false`), and the status follows the FEAT's PR (`TRACE sync-status`); a dropped FEAT becomes `cancelled` with the reason in History.

## 1. Confirm readiness

Require a NEED with `status: refined` whose REQs are `approved`; with `sdd.needs: false` (no NEED file), the request `sdd-specify` decided and the approved REQs `sdd-clarify` wrote, which land in this change, and Problem / value holds what the NEED would: the Request quote, the Triage block, the desired outcome, the Situations, scope and constraints. Read the actual modules/files plus repository rules, and the journeys and processes the NEED lists; do not infer structure from the desired design.

## 2. Cut the NEED into deliveries

- One FEAT per delivery: a set of whole REQs that ships and is proved on its own. Never a bucket FEAT that collects unrelated work or keeps taking rows; later work is a new NEED.
- One FEAT per use case, one actor and one goal, for the project's life (KIT-096): before creating a FEAT, find the one whose actor and goal or `processes` steps the delivery shares; the delivery is then that FEAT's next `## Versions` block (`### <version>` by `release.versioning`: `0.3.0`, or `M5`), never a second FEAT. A greybox and its polish are two blocks of one FEAT. Other steps or goals of one process are other FEATs.
- A NEED of type `platform` (tooling, CI, process) gets its own FEAT, never rows inside a product FEAT.
- Estimate each delivery's rows (one per verifiable outcome, `sdd-tasks` § 2). Above `max_feat_tasks`, split the NEED into several FEATs ordered by `depends_on`, or a versioned FEAT's work into the next block; `check_spec.py` fails an open version block above it and warns on a FEAT without `## Versions`.

## 3. Create each FEAT

- Take the next unused `FEAT-nnn` (or the session's reserved block) and create it from the template with `status: proposed`.
- `requirements`: the REQs this delivery implements, new or amended; add the FEAT to each of those REQs' `features` (both sides list the link). REQs left to another delivery stay in Out of scope.
- `processes` (with `docs/spec/processes/`): the process steps the use case realizes, `PROC-nnn S<a>–S<b>` (or `PROC-nnn`, `S<n>`, `A<n>`). The version block holds `Status: proposed`, its `Scope:` line (the REQs and ENB contracts it adds or changes, all in the frontmatter), its Plan delta, its task rows and its Closure; `spec_trace.py check` fails a block that serves an undeclared step, cites a REQ only undeclared steps cite or names an ENB outside `enablers` (the anti-bucket rule).
- Problem / value: one line and the NEED id; the NEED keeps the full problem, Situations and scope. Scope lists the REQs delivered.
- Acceptance criteria are technical (contract, unit, integration, e2e); each cites in `Proves` the REQ ids it proves, and every REQ in Scope is proved by at least one criterion. The REQs' examples and counterexamples are the functional criteria; do not restate them.
- `enablers` (only with `docs/spec/enablers/`): the ENBs this delivery creates or changes; `kind: enabler` marks a FEAT that changes ENBs and delivers no REQ-F.
- Passes (`sdd.passes: [greybox, polish]`; `[]`, the default, plans one pass; KIT-094): a NEED that adds a new mechanic (never a content route) is planned as two version blocks of one FEAT, `### <version> greybox` then `### <version> polish` (`### 0.3 greybox`, `### 0.3 polish`). The greybox block delivers the rules, Design, Contract and the Data tunables with placeholder art; it owns no Plan § Assets row and no feel value (a tunable's final value). The polish block owns § Assets and the feel values inside each tunable's range, amends no rule, and is written only after the owner's playtest line (`../sdd-review/references/playtest.md`). A rule change goes to `sdd-clarify`; a broken split is `sdd-check` C16.
- Add the FEAT to the NEED's `features` and a History line.

## 4. Write the Plan sections

`## Plan` holds one `### <section>` per name in `plan_sections`, in this order: Design, Contract, Data, UI, Assets, Flag, Tests, Observability, Risks, Dependencies (`Risks` and `Tests` always; `Assets` only when listed). Each holds its content or one line `— <why it does not apply>`. What each section holds: `references/plan-sections.md`. The standards each section applies:

| Section | Reference |
|---|---|
| Design | `references/architecture.md` (blocks: `references/pattern-catalog.md`); a trust boundary `references/security-design.md`; a service `references/twelve-factor.md`; a Godot client `references/godot/README.md` |
| Contract | `references/contract.md` |
| Data | `references/data.md` (versions `references/postgres-18.md`, `references/redis-7.md`) |
| Assets | `references/plan-sections.md` § Assets rows; the import: skill `sdd-implement`, reference `assets.md` |
| Tests | skill `sdd-implement`, references `tdd.md` and `test-gates.md` |

- The Plan is the design: every choice the rows need is made here, so a task cell points to `Plan § <section>` and never restates it.
- Design cites each process state the FEAT implements (`PROC-nnn` and the state name) with what holds it (a state machine, `references/pattern-catalog.md`), and each process step it serves; a state the Plan adds or drops goes back to `sdd-clarify` as a process change.
- Data maps each tunable of the FEAT's REQs (a Values row whose `Tunable` cell is not `fixed`) to its exposure: the content key, config entry or debug control the code reads it from, never a literal; `sdd-check` C14 flags one with no line.
- Assets: one row per asset the delivery needs (for a game, animations with frame counts, particles and sounds; for a business project, e-mail templates, copy, icons and translations), each with its source, its license and the REQ or mock it serves, so the art is made or bought before the cut.
- Contract: every changed message, endpoint, schema or table another FEAT reads passes the four checks of `references/contract.md`. With `docs/spec/enablers/`, the section cites each contract as its catalog row `ENB-nnn:<contract>` (`ENB-004:turn-result`) and states only the change; a new contract gets its Provided contracts row and `providesApis` id in this spec PR, and the contract PR corrects the row to what shipped (skill `sdd-implement`).
- Walk table (only with `docs/spec/enablers/`), at the end of Design: `| Step | REQ | ENB contract | Task |`, one row per process or journey step the FEAT serves (`PROC-nnn S2`; `—` for a REQ no step cites), each REQ of Scope in at least one row, the ENB contract that carries it (`ENB-nnn:<contract>`, or `ENB-nnn` for an aggregate with no contract), and `—` in Task until `sdd-tasks` writes the row ids. A REQ that no ENB satisfies gets its Aggregates or Qualities row in the owning ENB in this spec PR (`sdd-check` C18).
- Name real rooted files and the architecture areas of `docs/spec/spec.md` § Architecture each change lands in.

## 5. Record decisions

A technical choice with a rejected reasonable alternative that outlives the FEAT (other FEATs or later work rely on it) gets a decision record (`DEC-nnn`, or the prefix of its kind when `docs/spec/spec.md` declares `decision_kinds`) with `status: proposed`. A choice that matters only inside this delivery stays in its Plan section, the rejected alternative in one line. A product choice is not made here: it returns to `sdd-clarify`. Several open choices form a tree, as the questions of `sdd-clarify` § 2 do: settle only from its frontier, the choice the others depend on first, one choice per question when it needs the owner, and never one whose answer hinges on a choice still open. Do not hide a kit-rule exception in prose—record a blocker or explicit decision.

Fold settled decisions (the `decision_folding.marker` of the project profile, default `→ folded into`): a `[DECISION]` line settled in the FEAT's `## Open questions` is not edited or deleted. The next spec PR that touches the FEAT (a Plan amendment, the `sdd-tasks` rows, a resync) writes the decision where it belongs, as a Scope bullet, an acceptance criterion with its Given/When/Then, or the REQ (a REQ change goes through `sdd-clarify`), and appends the marker and the target to the line: `→ folded into CA-3`. Open questions lists the unfolded lines first. Task `Status` needs no folding: it is derived from the items (`sdd-tasks` § 5).

## 6. Check restraint and consistency

Do not add queue/cache/service/layer without demonstrated need. Ensure every criterion has a planned proof in Tests, run `sdd-check FEAT-nnn` (full scope: the functional items again plus the technical ones; C8's task half waits for `sdd-tasks`; with `docs/spec/enablers/`, C18 and C19 from both `spec_trace.py enablers` and `check`, and C25 from `spec_trace.py governance --feat FEAT-nnn`) with no critical/high findings, then set `status: planned` (and the open version block's `Status: planned`) and update History. From then on the block's Scope is frozen: a new or amended REQ goes to the next block (`sdd-check` C17).

Done when: each FEAT is one delivery within `max_feat_tasks`, lists the REQs it delivers on both sides, proves every REQ in Scope by a criterion, holds every `plan_sections` section (content or `— <why>`) naming real files, passes the contract checks, cites each contract by its catalog row and walks each step and REQ to an ENB contract when the project keeps enablers, gives each lasting choice a decision record and the full check is unblocked.
