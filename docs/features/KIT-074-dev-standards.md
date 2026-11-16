---
id: KIT-074
title: "A consumer project's generic dev standards become kit standards: doc-structure check, just modules per profile, gitleaks CLI template, keyed-CSV merge driver"
status: done
confirmed: "2026-11-15 (owner, chat relayed by the SDD review session: the tool comparison approved with \"Tudo num release só\", KIT-070, KIT-072, KIT-073 and KIT-074 in one release, 13.0.0)"
issue: "#258"
pr: "#263"
---

# KIT-074 — Dev standards into the kit

## Problem and evidence

[FACT] The kit named its daily commands only as prose, in two places that can drift: the project AGENTS templates
(`plugins/guardrails/templates/project-agents-*.md` § Commands) and, inline, the CI templates
(`platforms/kits/github/workflows/ci-godot.yml`, `ci-java.yml`). Nothing runnable was shared, so a consumer project
wrote its own wrapper: three justfiles (root, Godot client, Java server) delegating to three `dev.sh` scripts
(read 2026-11-15 at the consumer's `origin/main`). The two copies had already drifted: the AGENTS template's GUT
command scanned subfolders (`-ginclude_subdirs`) and CI's did not; the boot proof grepped `SCRIPT ERROR|Parser Error`
while `review_checks.py` (KIT-069) fails on `Can't load script`, `SCRIPT ERROR`, `Parse Error` and `Parser Error`.

[FACT] The same project keeps four generic tools the kit lacked (comparison of the consumer export `82ed724e4` with
kit `4f035d1`, 2026-11-15): a README/INDEX folder check (154 lines), a 3-way merge of a translation CSV by key (126
lines, run by hand or by its loop, while `.gitattributes` still says `merge=union`, which kept a branch's stale row
beside the edited row of the same key and reported no conflict, three times), a gitleaks CLI step pinned by version
and sha-256, and the generic part of its recipes.

[FACT] The kit's gitleaks template used `gitleaks/gitleaks-action`, which in an organization's repository needs a
`GITLEAKS_LICENSE` secret and exits 1 before scanning without one (the consumer's workflow README records the switch
to the CLI for that reason).

## Change

1. `platforms/ci/validations/check_docs_structure.py` (opt-in): from `git ls-files`, every authored folder has a
   `README.md` with a `# ` title and the configured headings, and every `done/` folder an `INDEX.md` naming each direct
   child. Parameters in `docs/spec/spec.md` `sdd.doc_structure` (`spec.schema.json`): `enabled` (default false),
   `exempt` (default `.github/doc-structure-exempt.txt`), `headings` (default `## What goes here`,
   `## What does not go here`), `done_index` (default true). Always exempt: `.github` itself (GitHub shows a
   `.github/README.md` in place of the root README) and the folders `sync-project.sh` generates. `sync-project.sh`
   vendors it into `.github/spec-lint/` while enabled and removes it when turned off; `--check` flags a leftover.
   The `spec.md` template that `init-spec.sh` copies (`plugins/guardrails/templates/spec-index.md`) carries the block
   with its defaults, like every other `sdd` key. The standard is written in KIT-070's homes: the `sdd-implement`
   living-docs reference (a checklist row and § Folder READMEs and done/ indexes) and `sdd-constitution`
   `references/sdd-parameters.md` (the key's row).
   The kit's own `check_kit.py` rule "INDEX.md only at plugins/<name>/" now says it is the kit repository's rule
   (`check_kit.py` message, `.github/CONTRIBUTING.md`).
2. `platforms/kits/just/{godot,java,python,docs}.just`: standard recipes `test`, `verify`, `fmt`, `lint`, `run` where
   it fits (godot adds `editor`, `import`, `boot`, `export PRESET OUT`; java `dependency-check`). Each command was
   classified generic, generic per stack or project-specific (`platforms/kits/just/README.md`); project-specific ones
   (fixed export names, `run-dev`, `db-shell`, compose paths, protocol and content checks) stay in the project's
   justfile. `platforms/tools/sync_just.py`, called by `sync-project.sh`, writes `kit.just` in each profile folder
   (`:<dir>` scoping), `kit-<profile>.just` modules plus shared recipes when one folder has several profiles, and a
   starter `justfile` with `import 'kit.just'` where a folder has none; it refuses an unmarked `kit.just`, a folder
   reached through a symbolic link and a `justfile` that is a symbolic link (dangling or not) or not a regular file
   (review of #263), removes marked modules no profile needs, and `--check` fails on drift or a
   justfile without the import. The AGENTS templates and `ci-godot.yml`/`ci-java.yml` call the same recipes (just
   1.58.0 from its release tarball, sha-256 checked); `check_kit.py` § 14 fails a template that names a recipe its
   module lacks, an AGENTS template without `just test` and `just verify`, and two different `just` pins.
3. `platforms/kits/github/workflows/gitleaks.yml`: the gitleaks CLI 8.30.1 pinned by sha-256, `--redact`, the whole
   history (`--log-opts=HEAD`), a `config` input, `.gitleaksignore` at the root; push, pull request, dispatch and
   `workflow_call` triggers. The action template is not kept. The scan standard (a branch range before the PR, the
   whole history in CI) goes into `security` (`references/scan.md` § 3, which § 2's exposure step cites), and `git`
   points to it. The template pins `actions/checkout` by commit SHA and keeps a 5-minute timeout, as KIT-076's
   `workflow-lint` requires.
4. `platforms/kits/godot/scripts/keyed_csv_merge.py`: a git merge driver (`merge=keyed-csv`) merging a keyed CSV row by
   row: the 3-way rule per key, a conflict written between git's markers at the key's place, `--key-column N`, quoted
   keys and multi-line quoted values, our order kept (sorted sides stay sorted), CRLF rows equal to LF ones, and a
   text merge (`git merge-file`) when a side does not parse. `sync-project.sh` vendors it into
   `.github/merge-drivers/` for a godot profile and prints the one-time `git config merge.keyed-csv.*` step; it never
   writes git config. A clone without the driver merges the file as text, so the conflict shows (checked).
5. KIT-072's pin (`--vendor-skills`) records the vendored driver (a byte copy of its kit source) and each generated
   `kit.just`/`kit-<profile>.just` (the file the sync wrote, listed by `sync_just.py list`) in `KIT_MANIFEST.json`
   `copies`, so `--check` reports a copy changed after the sync as `diverges from the pin`; bytecode beside the
   driver stays out (requested by the KIT-072 review).

## Proof

`bash platforms/tools/check.sh`, `CI=1 bash platforms/tools/check.sh`, `bash platforms/tools/smoke.sh`,
`python3 platforms/ci/validations/check_kit.py --links`, the suites `test_check_docs_structure`, `test_keyed_csv_merge`,
`test_just_modules`, `test_gitleaks_template`, `test_sync_dev_standards`, `test_sync_project`, `test_check_kit_readmes`,
`gitleaks git --redact --log-opts=origin/main..HEAD` and `platforms/tools/review_checks.py red`; results in the PR.

## Adoption actions (consumer resync, not run here)

- Each profile folder gets `kit.just`; add `import 'kit.just'` to its justfile and drop the project recipes the kit
  now provides under the same name; keep project recipes (exports, `run-dev`, `db-shell`, `up`/`down`, `gates`).
- Recopy `ci-godot.yml`/`ci-java.yml` (they need `kit.just` where they run) and `gitleaks.yml` with the project's config
  path as `config`; keep `.gitleaksignore`.
- Godot: replace `merge=union` on each translation CSV with `merge=keyed-csv` in `.gitattributes`; run the two
  `git config merge.keyed-csv.*` lines once per clone; move any tool that imports the old merge module to the driver.
- Doc structure: set `sdd.doc_structure.enabled: true` and `exempt: <path>` (the project's existing exempt list),
  rerun the sync, call `.github/spec-lint/check_docs_structure.py` (or `just lint`) from CI, delete the project's
  own copy.

## History

- 2026-11-15: confirmed (owner, through the SDD review session); issue #258.
- 2026-11-16: merged `main` with KIT-070, KIT-072, KIT-073 and KIT-076; the standards text moved to KIT-070's homes,
  the gitleaks template pinned for KIT-076's `workflow-lint`, the driver and modules added to KIT-072's pin.
