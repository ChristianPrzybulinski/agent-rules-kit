---
id: KIT-066
title: "Every request enters as a NEED-nnn intake record and is routed by type"
status: confirmed
confirmed: "2026-11-14 (owner, chat of the SDD review session: \"Aprovo, escrever\" for the NEED-nnn intake draft)"
issue: "#231"
pr: ""
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
  becomes one or more REQs. Triage gives type, artifacts touched, route, size and who confirmed. The frontmatter carries
  `type`, `status`, `origin`, `parent` and the forward links `requirements`, `journeys`, `decisions`, `debts` and
  `features`. A comment states which sections capture fills and which triage fills.
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
- `plugins/guardrails/skills/sdd-intake/` (new skill, user and model, Codex implicit invocation allowed): capture,
  triage, hand-off and validation. In triage the first matching type wins. A `fix` needs an artifact that already states
  the right behavior, otherwise it is an improvement. `fix` and `content` close `routed`. Duplicates close `merged`,
  ideas for later `parked` and refused ones `rejected` with the reason. Product confirms type and route. The agent
  opens with a verdict and asks one question at a time. `/grilling` and `sdd-spike` are tools inside triage. No topic
  owner existed: `sdd-specify` writes FEAT/REQ criteria, and routing also ends in fix rows, data changes and decisions
  (KIT-039).
- `plugins/guardrails/skills/sdd-constitution/references/sdd-process.md`: one entry (`sdd-intake`) replaces the five.
  The flow table gains the entry row. Identifiers, id blocks, the NEED status flow, when `refined` and `delivered`
  apply, spec-first for NEED files and the `needs/` folder are written in.
- `plugins/guardrails/skills/sdd-specify/SKILL.md`: starts from a triaged NEED with route `refine`, and writes its FEAT
  and REQ ids, the Refinement rows and a History line back into the NEED.
- `plugins/guardrails/skills/sdd-clarify/SKILL.md`: sets the NEED `refined` when all its FEATs are clarified and its
  decision records approved.
- `plugins/guardrails/skills/sdd-constitution/SKILL.md` and `plugins/guardrails/templates/spec-index.md`: a `needs/`
  folder, a Needs index and NEED files as spec-first.
- `plugins/guardrails/rules/spec.md`: `spec-need.md` and `NEED-nnn` in the lists. New line: never list a NEED in a REQ,
  FEAT, decision or debt. Only a NEED's verbatim Request keeps the asker's language.
- `platforms/kits/sdd/init-spec.sh` creates `needs/`. `platforms/tools/sync-project.sh` copies `need.schema.json`.
  `platforms/tools/sync-profiles.txt` gives `sdd-intake` to the `docs` profile. `check_kit.py` maps `spec-need` to its
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
