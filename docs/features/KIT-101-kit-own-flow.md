---
id: KIT-101
title: "The kit runs its own FEAT-only flow: kind tooling, KIT ids and a spec root of its own"
status: in-progress
confirmed: "2026-11-16 (owner, kit chat: \"Sim, faça\" on E § 17, backlog G8)"
issue: "#343"
pr: ""
---

# KIT-101 — The kit runs its own FEAT-only flow: kind tooling, KIT ids and a spec root of its own

## Problem and evidence

[FACT] The game-profile evaluation (`KIT-GAME-PROFILE-EVALUATION-2026-11-16.md` in the owner's workspace, "E"),
§§ 10 and 17.3, backlog G8: the kit's own process was prose in `docs/features/README.md` that no skill read. Its
`.ai-kit.yaml` (KIT-087 P1b) left `sdd` at its defaults "because no key could describe the kit's records". KIT-100
made the FEAT-only flow run.

[FACT] Probe on a copy of `docs/` with `spec_root: docs`, `kind: tooling`, `id_prefix: {feature: KIT}`:
`check_spec.py` reports 96 FAIL lines with jsonschema (94 `schema`, 1 `frontmatter` for `README.md`, 1 `id-file` for
`TEMPLATE.md`) and 366 without it, since the old records carry `status: done`, `confirmed` and no `created`. A
`baseline.json` holds a count per rule and artifact, so the two modes cannot share one, and the records must stay as
they are.

## Change

- `.ai-kit.yaml`: `project.kind: tooling` and `sdd.id_prefix.feature: KIT`. `sdd.flow` resolves to `feat-only` from
  the tooling preset and `spec_root` to its default `docs/spec`; both are named in the file's comments, not written,
  because the `KitOwnProfile` contract test (KIT-087 P1b) fails a key set to its default (it failed on both when they
  were written). Decision: `spec_root` is `docs/spec`, not `docs`, so no validator reads the old records (evidence
  above); new records are `docs/spec/features/KIT-nnn-slug.md`.
- `docs/spec/spec.md` from `spec-index-tooling.md` (no `sdd:` block), and `features/`, `decisions/`, `debts/` with
  `.gitkeep`, as `init-spec.sh` creates them for kind tooling.
- `docs/features/README.md`: the Process section points at the skills (`sdd-plan` with the lite template, `sdd-check`,
  `sdd-implement`, `review`, `spec_trace.py sync-status`); the records up to KIT-101 stay in their own format.
  `.github/CONTRIBUTING.md`'s kit-feature row says the same.
- `platforms/ci/validations/test_kit_own_spec.py` (new): the profile resolves to the tooling flow with no note, the
  kit's spec passes `check_spec.py` in both modes and `spec_trace.py check`, and no old record lies under
  `spec_root`.

## Proof

[FACT] On branch `feat/kit-101-kit-own-flow`, from `feat/kit-100-feat-only-flow`, macOS:

- Red first: `test_kit_own_spec.py` failed 3 of 4 before the change (profile, spec, trace), all pass after, under
  `python3.12` and `/usr/bin/python3` 3.9.6.
- `check_kit.py` § 15 (`profile.py resolve` exit 0 with no note) passes inside `check.sh`.
- `bash platforms/tools/check.sh` and `--links`: `check: OK (1 plugins, 18 skills, 11 rules, 18 templates, 15 readmes,
  174 links, 65 hook cases, 18 shell scripts)`.
- `python3.12 platforms/tools/run_tests.py --layer unit,contract`: `OK (skipped=16)` (gdtoolkit); `--layer
  integration --changed-from origin/main`: `OK (skipped=1)` (a non-UTF-8 file name).
- Not verified: a real KIT record written through `sdd-plan` and delivered by `sync-status` against GitHub.

## History

- 2026-11-16: confirmed (owner, kit chat; issue #343).
- 2026-11-17: implemented on `feat/kit-101-kit-own-flow`.
