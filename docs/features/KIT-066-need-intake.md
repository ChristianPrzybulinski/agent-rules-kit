---
id: KIT-066
title: "One entry and a functional front chain: NEED → REQs → FEAT (intake, specify, clarify, plan)"
status: confirmed
confirmed: "2026-11-14 (owner, chat of the SDD review session: \"Aprovo, escrever\" for the NEED-nnn draft; \"aprovo sua ideia. importante os templates e escopos bem definido\" for the front chain; \"ok, aprovo\" for sdd-check as a tool)"
issue: "#231"
pr: "#232"
---

# KIT-066 — One entry and a functional front chain: NEED → REQs → FEAT

## Problem and evidence

[FACT] At `3807c85`, `plugins/guardrails/skills/sdd-constitution/references/sdd-process.md` lists five entry points:
`/grilling` for a vague idea, `sdd-specify` for a described feature, `sdd-constitution`, `sdd-journey` and `sdd-spike`.
None records a request before it is judged, and none tells new work from an improvement or a fix.

[FACT] In a consumer project, the owner's ideas of 2026-11-13 and 2026-11-14 entered through four proposal files kept in
the owner's workspace folder, which is not a git repository: no id, no version, no link to the requirements and
decisions they produced, no validation. Its newest feature (written 2026-11-14) cites one of them as its evidence.

[FACT] `sdd-specify` writes the FEAT and its REQs together, so the business problem, the functional rules and the
technical criteria share one file. In that consumer feature, a criterion repeats the examples of one of its REQs, three
criteria are technical proofs (contract examples, a generator command, rejected client frames), and that REQ's
Statement is two paragraphs carrying the random draw, its order and a retry fallback. Across the consumer's 609 REQs on
2026-11-14 the Statement has a median of 74 words (p90 127, max 529) against the template's one testable sentence; 578
carry counterexamples and 70 a History section, which the kit templates lack; 18 are REQ-NF.

[FACT] `platforms/ci/validations/check_spec.py` validated only `features/`, `requirements/`, `decisions/` and `debts/`,
and failed every REQ with no FEAT, so a REQ could not exist before the FEAT that delivers it. The kit's spec layer is
file-based: among the skills only `git`, `sdd-to-card` and `investigate` mention `gh` or GitHub, so the owner chose a
file over an issue for the entry.

[FACT] `sdd-journey` was a separate step; the consumer feature above says "Journey: none yet".

[FACT] The two side doors had no way back in: `sdd-plan` sends a load-bearing risk whose test needs code to `sdd-spike`,
whose §1 accepted only feel questions and whose deliverables went to an issue; `investigate` ended in a report with no
destination. The consumer's glossary holds 21 terms on 2026-11-14, about half of them process terms, while its client
has 25 feature folders whose domain names (trade, guild, daycare, duel, battle) have no glossary row.

## Change

The chain becomes `sdd-intake` → `sdd-specify` → `sdd-clarify` → `sdd-plan` → `sdd-tasks` → `sdd-to-card` →
`sdd-implement` → `review`. Each step owns one artifact and one status move: the NEED (business), the REQs (functional),
the FEAT (technical). `sdd-check` leaves the chain and becomes the read-only tool that clarify and plan call.

- `plugins/guardrails/templates/spec-need.md`: the `NEED-nnn` template (verbatim Request, Problem / value, Desired
  outcome, Situations, Scope, Out of scope, Constraints, Evidence, Triage with type, artifacts touched, route, size,
  priority and who confirmed, Open questions, Refinement, History). Each section's comment names the step that fills it.
  Status `proposed → triaged → specified → refined → delivered`, or closed `rejected|merged|routed|parked`.
- `plugins/guardrails/skills/sdd-intake/` (new, user and model): records only, ends at `proposed`.
- `plugins/guardrails/skills/sdd-specify/` (now user and model, Codex implicit invocation allowed): part 1 decides
  (type table, a `fix` only when an artifact already states the right behavior, duplicates, size, priority
  `now|next|later`, route, verdict and one question at a time; product confirms product choices, the agent routes a
  fix or a duplicate and product reviews later) → `triaged` or closed; part 2 describes with product (outcome,
  Situations right and wrong, scope, constraints, evidence) → `specified`. It writes no REQ, FEAT, decision or debt.
- `plugins/guardrails/skills/sdd-clarify/`: the functional refinement. Each Situation becomes a reused, amended or new
  REQ, a journey step, a product decision or a cut; questions go one at a time; the NEED's Refinement table and links are
  filled; after a clean functional `sdd-check` and product approval the REQs become `approved` and the NEED `refined`.
  New references: `references/req-scope.md` (what a REQ holds and what goes elsewhere, REQ-F versus REQ-NF, when to
  split or keep one, what a NEED touches) and `references/journeys.md` (the journey rules, written inside clarify).
  Each Situation is worked as an example map (rules become REQs, examples and counterexamples their Verification,
  unknowns the questions); a size L NEED or a new area may start with an event-storming pass; an invariant is a REQ of
  its own; every domain term a REQ uses is in the `spec.md` glossary; a screen REQ cites the mock product approved
  (`spec-requirement-functional.md` gains a `Mock` line); the next question is one no open question decides.
- `sdd-spike` also takes technical feasibility questions (a risk `sdd-plan` names whose cheapest test needs code), and
  without a tracker its report goes to the project's collaboration folder, cited in the NEED's Evidence; the kept idea
  re-enters through that NEED. `investigate` hands its report to `sdd-intake` as a NEED (`fix` when an artifact states
  the right behavior, otherwise `improvement`) with the failing test in Evidence. `sdd-intake` cites such a report in
  Evidence.
- `sdd-journey` is removed as a skill; its rules live in `sdd-clarify/references/journeys.md`. `sdd-triage`, added
  earlier on this branch, is folded into `sdd-specify`. A consumer that vendors skills keeps its old `sdd-journey` copy
  until its resync.
- `plugins/guardrails/skills/sdd-check/`: no longer a numbered step but a tool, still user and model invocable for audits
  (`all`). Functional scope (`NEED-nnn`, called by `sdd-clarify`, blocks `refined`): C1 (NEED→REQ), C2, C4, C5, C6, the
  new C11 (a REQ states how instead of what: algorithm, message, table, framework; medium; it enforces `req-scope.md`),
  the journey links, Q1 read against each REQ's Verification, Q2–Q4 and Q7. Full scope (`FEAT-nnn`, called by
  `sdd-plan`, blocks `planned`): the functional items again (C1 as FEAT↔REQ, Q1 against the FEAT's criteria) plus C3,
  C7–C10, Q5, Q6 and Q8–Q11; C8's criterion↔task half waits until the task rows exist.
- `plugins/guardrails/skills/sdd-plan/`: starts at a `refined` NEED and creates the FEAT, one delivery: the REQs it
  implements on both sides, technical acceptance criteria that cite the REQs they prove, then the Plan and technical
  decisions; `planned` after a clean full-scope check. `sdd-tasks` notes that criteria cite REQs.
- Templates: `spec-requirement-functional.md` and `spec-requirement-non-functional.md` gain `status`
  (`proposed|approved|retired`, absent = approved), `source: NEED-nnn S<n>`, a one-sentence Statement with a Values table
  (no algorithm), counterexamples in Verification and a `## History`. `spec-feature.md` is created by `sdd-plan`: one
  line plus the NEED id, Scope lists the REQs delivered, and the criteria table gains a `Proves` column.
- `platforms/ci/schemas/need.schema.json` (new) and `requirement.schema.json` (optional `status`).
  `platforms/ci/validations/check_spec.py` validates `needs/` at its top level only, so a `NEED-nnn-data/` folder holds
  any evidence (kinds and existence of every link, journeys by file, `parent`, `refined`/`delivered` backed by links,
  `delivered` only with delivered FEATs, or for a `decision` NEED with no FEAT an approved decision, `NEED` reserved as a
  decision prefix) and accepts a REQ with no FEAT when an open NEED lists it (a delivered, rejected, merged, routed or
  parked one does not count). `spec_trace.py` lets a main or alternative journey step hold a literal `—` in
  `Implemented by` and `Proven by` while a NEED that lists the journey in `journeys` is open (not delivered, rejected,
  merged, routed or parked), so a step written in clarify does not block `refined`; once no open NEED lists the journey
  both are required, as on `main`, and a project without `needs/` keeps `main`'s rule. A prerequisite row, an empty
  cell and a journey with no step still fail. `sdd-tasks` fills both cells when it cuts the rows. `test_check_spec.py`
  adds `NeedTest` (20 tests) and `DecisionKindsTest.test_need_prefix_is_reserved`, each in full and structural mode;
  `test_spec_trace.py` adds `PendingStepTest` (8 tests).
- Text: `sdd-process.md` (entry, chain, flow table with `sdd-check` as a tool in place of step 3, NEED/REQ/FEAT statuses),
  `rules/spec.md` (templates, ids, link rule, NEED provenance, Request language), `sdd-constitution` and
  `spec-index.md` (`needs/`, Needs index), `init-spec.sh`, `sync-project.sh` (copies `need.schema.json`),
  `sync-profiles.txt`, `check_kit.py` (`spec-need` schema map), `platforms/ci/README.md`, `docs/projects.md`, `INDEX.md`.

A consumer must resync (`sync-project.sh`) before writing a REQ `status` or a NEED: its old schemas refuse both.

Follow-ups, outside this record: project parameters in `spec.md` to turn NEEDs, journeys or the issue tracker off; a
generated reverse view (NEED ← REQ/FEAT); a consumer project's adoption (its process decision, `docs/spec/needs/`, the
resync and its report triage).

## Proof

`bash platforms/tools/check.sh` (also with `CI=1`), `bash platforms/tools/smoke.sh`,
`python3 platforms/ci/validations/check_kit.py --links`, the `test_check_spec`, `test_spec_trace` and `test_sync_project`
suites, and `gitleaks git --redact --log-opts=origin/main..HEAD`. With `origin/main`'s `check_spec.py` and schemas, 10
of the 14 new tests fail. Of the 4 that pass, 3 assert that valid NEEDs pass, which the old checker allows because it
ignores `needs/`, and 1 refuses an unknown REQ status, which the old schema refuses because it allows no `status`.
Results are in the PR body.
Of the first review round's 12 new or changed tests, 5 failed against the checkers of `46c2602`. Of the second round's
10 new or changed tests (`PendingStepTest`, `test_main_step_without_tests_fails` restored to its `main` form, and
`NeedTest.test_req_listed_only_by_a_delivered_need_fails`), 6 fail against the checkers of `da2f9a8` (11 failures with
subtests): a step whose open NEED is settled, the amend path, the step with no rule, the project without `needs/`,
`main`'s test of a step without tests and the REQ listed only by a delivered NEED. The 4 that pass there guard what must
not change: a step waits while its NEED is open, an empty cell, a prerequisite row and a journey with no step still
fail.

## History

- 2026-11-14: confirmed (owner, chat).
- 2026-11-14: entry split into `sdd-intake` and `sdd-triage`, priority added (owner, chat: "ok concordo com os ajustes",
  "sim 2 skills").
- 2026-11-14: front chain (owner, chat: "sim só no REQ, concordo"; "aprovo sua ideia. importante os templates e escopos
  bem definido"): triage folds into `sdd-specify` with a `specified` status, `sdd-clarify` writes the REQs, journeys
  move inside clarify and check, `sdd-plan` creates the FEAT, REQ status and REQ-before-FEAT.
- 2026-11-14: `sdd-check` becomes a tool that `sdd-clarify` (functional scope) and `sdd-plan` (full scope) call, and
  gains C11 for a REQ that states how instead of what (owner, chat: "ok, aprovo").
- 2026-11-14: example mapping, event storming for large NEEDs, invariants, domain glossary and screen mocks in
  `sdd-clarify`; `investigate` and `sdd-spike` re-enter through `sdd-intake`; the spike takes feasibility questions
  (owner, chat: "concordo com sua proposta" for the development and clarify proposal, "concordo" for the side doors,
  "aprovo" for the split that puts them in this record).
- 2026-11-14: review fix round (independent review NOT READY): a journey step holds `—` until a FEAT listing one of its
  REQs is validated or delivered, so clarify's new steps no longer deadlock `refined` (orchestrator's design, journeys
  stay in clarify as the owner approved); `check_spec.py` skips `NEED-nnn-data/` folders, lets a `decision` NEED with an
  approved decision and no FEAT be `delivered` and ignores REQs listed only by closed NEEDs; `sdd-check` rows and
  checklist items match the stage they run in (C1, C8, Q1, Q5, Q6); nits in `sdd-clarify`, `sdd-specify` and
  `spec-need.md`; `req-scope.md` cites a decision in Rationale, not `source`, and `rules/spec.md` says open NEED.
- 2026-11-14: second review round (delta review PARTIAL): the `—` wait follows the open NEED, not FEAT status. A step
  waits while an open NEED lists its journey, which fixes the amend path (a new step citing a REQ an older FEAT already
  delivered failed at once) and the step with no rule (it could keep `—` forever); without `needs/` the rule is
  `main`'s. `sdd-tasks` fills both cells; a delivered NEED no longer counts as listing a REQ; `platforms/ci/README.md`
  and `spec-journey.md` state the rules (orchestrator's design).
- 2026-11-14: `sdd-tasks` also fills a journey step whose `Rules` is `—`, and writes test task rows in `Proven by` until
  the test file exists (gaps the second round's executor reported).
