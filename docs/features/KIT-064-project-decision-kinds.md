---
id: KIT-064
title: "Each project declares its decision kinds and id prefixes; the kit names none of its own"
status: done
confirmed: "2026-11-13 (owner, chat of the session that removed the consumer project's names from the kit: \"Sim, começar aqui\" for the MINOR with configurable decision prefixes and a neutral default)"
issue: "#225"
pr: "#226"
---

# KIT-064 — Each project declares its decision kinds and id prefixes; the kit names none of its own

## Problem and evidence

[FACT] The kit is meant to serve any project. At `038c493`, `platforms/ci/validations/check_spec.py:96` and
`platforms/ci/schemas/decision.schema.json` accept only `^(DTEC|DGME|DPRO)-[0-9]{3,}$`, the schema's `kind` enum is
`tech`, `game` and `process`, and `check_spec.py:240` ties `game` to `DGME`. These are one consumer project's
prefixes. A new project's `docs/spec/decisions/DEC-001-*.md` fails with `id=DEC-001 != file name prefix`. Outside the
history, `git grep -w -E 'DTEC|DGME|DPRO'` finds 33 lines in 18 files: rules, `sdd-*` skills, templates, docs and
fixtures.

[FACT] The matrix header that the kit's `spec_trace.py generate` writes cites that project's tool path
(`tools/spec-trace/`) and decision `DPRO-013`. That project generates its own matrix with its own diverged tool,
`platform/tools/spec-trace/spec_trace.py`, whose header names `platform/tools/spec-trace/`. So the kit's header text
matches no consumer and binds none.

[FACT] `sdd-spike`, `testing`, `code-standards` and two templates give that project's game examples ("game feel",
"battle feedback", "capture chance, XP", "battle action").

## Change

- `platforms/ci/schemas/spec.schema.json`: optional `decision_kinds`, an object mapping each decision kind
  (`^[a-z][a-z0-9-]*$`) to its id prefix (`^[A-Z][A-Z0-9]{1,7}$`).
- `platforms/ci/schemas/decision.schema.json`: `id`, `supersedes` and `superseded_by` accept any
  `^[A-Z][A-Z0-9]{1,7}-[0-9]{3,}$`. `kind` is optional, with no enum.
- `platforms/ci/validations/check_spec.py` reads `decision_kinds` from `spec.md`, the first target. Without it, a
  decision id must be `DEC-nnn`. With it, `kind` is required and must be a declared key, and the id carries that kind's
  prefix. A declaration fails on a malformed kind or prefix, a prefix used twice, or a reserved one (`FEAT`, `REQ`,
  `DEBT`, `J`). The file-name check accepts any prefix and leaves its validity to these checks. The minimal parser
  reads a one-line `{k: v}` map, so the structural mode enforces the same rules.
- `platforms/ci/validations/test_check_spec.py` adds `DecisionKindsTest`. It has 9 tests, each run in full mode and in
  structural mode (`python -S` hides pyyaml and jsonschema). With the `origin/main` checker and schemas, all 9 fail.
- The text says `DEC-nnn` or the declared prefixes: `rules/spec.md`, `sdd-constitution` (and `sdd-process.md`),
  `sdd-plan`, `sdd-spike`, `code-standards/references/living-docs.md`, the `spec-decision`,
  `spec-requirement-functional`, `doc-spike-report` and `project-agents-*` templates, `docs/projects.md`,
  `platforms/ci/README.md`, `platforms/kits/sdd/progress.example.json` and the `test_sync_project.py` fixture. The
  `spec_trace.py` matrix header names no path or decision id. The game examples become neutral, and
  `testing`/`code-standards` say "game rules" where they said "battle".

Consequence for a consumer with `DTEC`/`DGME`/`DPRO` records: its resync PR (`sync-project.sh`, after the release)
also adds `decision_kinds: {tech: DTEC, game: DGME, process: DPRO}` to `docs/spec/spec.md`. The key cannot land
earlier, because the current `spec.schema.json` has `additionalProperties: false`. That project's `traceability.md` is
not affected, because its own tool writes it.

## Proof

`bash platforms/tools/check.sh` (also with `CI=1`), `bash platforms/tools/smoke.sh`,
`python3 platforms/ci/validations/check_kit.py --links`, the `test_check_spec`, `test_spec_trace` and
`test_sync_project` suites, `gitleaks git --redact --log-opts=origin/main..HEAD`, and a corpus run on a copy of the
consumer's `docs/spec`. Without the declaration, its 141 decision records fail. With it, the result is the same
`spec: OK (801 artifacts)` as that project's current checker, in full and in structural mode. Results are in the PR
body.

## History

- 2026-11-13: confirmed (owner, chat).
- 2026-11-13: done (PR #226).
