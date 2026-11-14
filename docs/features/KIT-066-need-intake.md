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
- `sdd-journey` is removed as a skill; its rules live in `sdd-clarify/references/journeys.md`. `sdd-triage`, added
  earlier on this branch, is folded into `sdd-specify`. A consumer that vendors skills keeps its old `sdd-journey` copy
  until its resync.
- `plugins/guardrails/skills/sdd-check/`: no longer a numbered step but a tool, still user and model invocable for audits
  (`all`). Functional scope (`NEED-nnn`, called by `sdd-clarify`, blocks `refined`): C1, C2, C4, C5, C6, the new C11 (a
  REQ states how instead of what: algorithm, message, table, framework; medium; it enforces `req-scope.md`), the journey
  links and Q1–Q7. Full scope (`FEAT-nnn`, called by `sdd-plan`, blocks `planned`): the functional items again plus C3,
  C7–C10 and Q8–Q11.
- `plugins/guardrails/skills/sdd-plan/`: starts at a `refined` NEED and creates the FEAT, one delivery: the REQs it
  implements on both sides, technical acceptance criteria that cite the REQs they prove, then the Plan and technical
  decisions; `planned` after a clean full-scope check. `sdd-tasks` notes that criteria cite REQs.
- Templates: `spec-requirement-functional.md` and `spec-requirement-non-functional.md` gain `status`
  (`proposed|approved|retired`, absent = approved), `source: NEED-nnn S<n>`, a one-sentence Statement with a Values table
  (no algorithm), counterexamples in Verification and a `## History`. `spec-feature.md` is created by `sdd-plan`: one
  line plus the NEED id, Scope lists the REQs delivered, and the criteria table gains a `Proves` column.
- `platforms/ci/schemas/need.schema.json` (new) and `requirement.schema.json` (optional `status`).
  `platforms/ci/validations/check_spec.py` validates `needs/` (kinds and existence of every link, journeys by file,
  `parent`, `refined`/`delivered` backed by links, `delivered` only with delivered FEATs, `NEED` reserved as a decision
  prefix) and accepts a REQ with no FEAT when a NEED lists it. `spec_trace.py` has no such rule and is unchanged.
  `test_check_spec.py` adds `NeedTest` (13 tests) and `DecisionKindsTest.test_need_prefix_is_reserved`, each in full and
  structural mode.
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

## History

- 2026-11-14: confirmed (owner, chat).
- 2026-11-14: entry split into `sdd-intake` and `sdd-triage`, priority added (owner, chat: "ok concordo com os ajustes",
  "sim 2 skills").
- 2026-11-14: front chain (owner, chat: "sim só no REQ, concordo"; "aprovo sua ideia. importante os templates e escopos
  bem definido"): triage folds into `sdd-specify` with a `specified` status, `sdd-clarify` writes the REQs, journeys
  move inside clarify and check, `sdd-plan` creates the FEAT, REQ status and REQ-before-FEAT.
- 2026-11-14: `sdd-check` becomes a tool that `sdd-clarify` (functional scope) and `sdd-plan` (full scope) call, and
  gains C11 for a REQ that states how instead of what (owner, chat: "ok, aprovo").
