---
id: KIT-066
title: "Every request enters as a NEED-nnn intake record and is routed by type"
status: confirmed
confirmed: "2026-11-14 (owner, chat of the SDD review session: \"Aprovo, escrever\" for the NEED-nnn intake draft)"
issue: "#231"
pr: "#232"
---

# KIT-066 — Every request enters as a NEED-nnn intake record and is routed by type

## Problem and evidence

[FACT] At `3807c85`, `plugins/guardrails/skills/sdd-constitution/references/sdd-process.md` lists five entry points:
`/grilling` for a vague idea, `sdd-specify` for a described feature, `sdd-constitution`, `sdd-journey` and `sdd-spike`.
None records a request before it is judged, and none tells new work from an improvement or a fix. `investigate` names a
bug's cause, and no step says how a reproduced bug becomes work.

[FACT] In a consumer project, the owner's ideas of 2026-11-13 and 2026-11-14 entered through four proposal files kept in
the owner's workspace folder, which is not a git repository. They had no id, no version, no link to the requirements and
decisions they produced, and no validation. The project's collaboration README says open proposals live in its
`docs/collab/`, so they had two homes.

[FACT] `platforms/ci/validations/check_spec.py` validates only `features/`, `requirements/`, `decisions/` and `debts/`
(the `targets` loop of `main()`). A new artifact folder is ignored.

[FACT] The kit's spec layer, from `sdd-specify` to `sdd-tasks`, is file-based. Among the skills only `git` (9 lines),
`sdd-to-card` (6) and `investigate` (1) mention `gh` or GitHub. An entry made of issues would bind the spec layer to
GitHub, which it does not need today. The owner rejected that option for this reason and chose a file.

## Change

- `plugins/guardrails/templates/spec-need.md`: the `NEED-nnn` template. The sections are the verbatim Request (date and
  channel), Problem / value, Desired outcome, Situations, Scope, Out of scope, Constraints, Evidence, Triage, Open
  questions, Refinement and History. Situations are plain-language cases, at least one right and one wrong, and each
  becomes one or more REQs. Triage gives type, artifacts touched, route, size, priority and who confirmed (product, or the agent for a fix or a
  duplicate). The frontmatter carries
  `type`, `status`, `origin`, `parent` and the forward links `requirements`, `journeys`, `decisions`, `debts` and
  `features`. Comments state who fills each section: capture fills the Request and one line of Problem / value, triage completes
  Problem / value and the Triage block, and `sdd-specify` fills Desired outcome, Situations, Scope, Out of scope and
  Constraints at the start of refinement. Evidence is filled at any step.
- `platforms/ci/schemas/need.schema.json`: required `id`, `title`, `type`, `status`, `origin` and `created`. `type` is
  `new|improvement|fix|content|platform|decision`. `status` is
  `proposed|triaged|refined|delivered|rejected|merged|routed|parked`. Each link list has its id pattern.
- `platforms/ci/validations/check_spec.py`: validates `docs/spec/needs/` by schema, or structurally without
  pyyaml/jsonschema. It checks that the id equals the file name prefix, that each listed id exists with the right kind,
  that each listed journey has a file under `journeys/` and that `parent` is another NEED. A `refined` or `delivered`
  NEED must name at least one requirement, journey or decision. A `delivered` one must list FEATs, all of them
  `delivered`. `NEED` joins the reserved decision prefixes.
- `platforms/ci/validations/test_check_spec.py`: `NeedTest` (9 tests, each in full and structural mode), plus
  `DecisionKindsTest.test_need_prefix_is_reserved`.
- `plugins/guardrails/skills/sdd-intake/` (new skill, user and model, Codex implicit invocation allowed) records only.
  It takes the next id or the reserved block and writes the file from the template, keeping every section. It fills the
  title, a provisional type, `origin`, the verbatim Request and one line of Problem / value, with `—` elsewhere. It
  splits a request holding several needs (`parent`), adds a History line and validates, ending at `proposed`. It never
  judges and reads only `needs/` and `spec.md`.
- `plugins/guardrails/skills/sdd-triage/` (new skill, user and model, Codex implicit invocation allowed) decides only.
  It reads `spec.md`, the touched REQs, journeys and FEATs, and `needs/` for a duplicate. It classifies by the type
  table; first match wins, and a `fix` needs an artifact that already states the right behavior, otherwise it is an
  improvement. It completes Problem / value and sets Size (S|M|L, no duration), Priority (`now`, `next`, `later`;
  `later` = `parked`) and Route, then sets `triaged` or closes `routed`, `merged`, `rejected` or `parked`. It gives a
  verdict with evidence, then asks one question at a time; `/grilling` and `sdd-spike` are tools inside it.
  - Product confirms `new`, `improvement`, `platform` and `decision`, a `content` value, a rejection and a park.
  - The agent routes a `fix` that cites the violated artifact's path and a duplicate that names the NEED kept,
    recording `Confirmed by: agent (fix|duplicate), product reviews later`.
  - Triage never fills Desired outcome, Situations, Scope, Out of scope or Constraints.
  - Owner-approved split (chat, 2026-11-14: "ok concordo com os ajustes", "sim 2 skills"): capture and judgment are
    different acts at different times. No topic owner existed: `sdd-specify` writes FEAT/REQ criteria, and triage
    also ends in fix rows, data changes and decisions (KIT-039).
- `plugins/guardrails/skills/sdd-constitution/references/sdd-process.md`: one entry (`sdd-intake`, then `sdd-triage`)
  replaces the five, and the flow table gains the `entry` and `triage` rows. Identifiers, id blocks, the NEED status flow, when `refined` and `delivered`
  apply, spec-first for NEED files and the `needs/` folder are written in.
- `plugins/guardrails/skills/sdd-specify/SKILL.md`: starts from a triaged NEED with route `refine`. With product, it
  first fills the NEED's Desired outcome, Situations (at least one that goes right and one that goes wrong), Scope, Out
  of scope, Constraints and Evidence. It then writes FEAT/REQs as before and writes their ids, the Refinement rows and
  a History line back into the NEED.
- `plugins/guardrails/skills/sdd-clarify/SKILL.md`: sets the NEED `refined` when all its FEATs are clarified and its
  decision records approved.
- `plugins/guardrails/skills/sdd-constitution/SKILL.md` and `plugins/guardrails/templates/spec-index.md`: a `needs/`
  folder, a Needs index and NEED files as spec-first.
- `plugins/guardrails/rules/spec.md`: `spec-need.md` and `NEED-nnn` in the lists. New line: never list a NEED in a REQ,
  FEAT, decision or debt. Only a NEED's verbatim Request keeps the asker's language.
- `platforms/kits/sdd/init-spec.sh` creates `needs/`. `platforms/tools/sync-project.sh` copies `need.schema.json`.
  `platforms/tools/sync-profiles.txt` gives `sdd-intake` and `sdd-triage` to the `docs` profile. `check_kit.py` maps `spec-need` to its
  schema. `platforms/ci/README.md` and `docs/projects.md` name the schema, folder and id. `plugins/guardrails/INDEX.md`
  is regenerated.

Out of scope, follow-ups for the next steps of the same review:
- a `## History` section in the REQ templates;
- REQ before FEAT (phase 2), which needs `check_spec.py`'s "has no FEAT implementing it" rule relaxed for an
  unscheduled REQ;
- a generated reverse view (NEED ← REQ/FEAT);
- a consumer project's adoption: its process decision, its `docs/spec/needs/`, the resync after the release, and its
  report-triage path to NEED or fix row.

## Proof

`bash platforms/tools/check.sh` (also with `CI=1`), `bash platforms/tools/smoke.sh`,
`python3 platforms/ci/validations/check_kit.py --links`, the `test_check_spec`, `test_spec_trace` and `test_sync_project`
suites, and `gitleaks git --redact --log-opts=origin/main..HEAD`. With `origin/main`'s `check_spec.py` and schemas, 8 of
the 10 new tests fail. The other 2 assert that valid NEEDs pass, and the old checker passes them only because it ignores
`needs/`. Results are in the PR body.

## History

- 2026-11-14: confirmed (owner, chat).
- 2026-11-14: entry split into `sdd-intake` and `sdd-triage`, priority added (owner, chat: "ok concordo com os ajustes",
  "sim 2 skills").
