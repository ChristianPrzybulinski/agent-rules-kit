# P3-02 — gdtoolkit lint and format in the Godot CI kit and in stratics-client

Phase: 3 · Repos: kit, stratics-client, stratics-docs · Branch to create: feat/p3-02-gdtoolkit-ci from main (one branch with the same name in each repo) · Depends on: P1-05, P2-07 · Effort: ~4 h

## Goal

The Godot CI kit and the Stratics client gain a deterministic style gate: `gdformat --check` and `gdlint` (gdtoolkit 4.5.0, pinned) run in CI over every project script outside `addons/` and `.godot/`, with one `gdlintrc` shipped by the kit and copied to the project. stratics-client gets a one-time formatting baseline so the gate starts green. Measurable result: `gdformat --check` on stratics-client goes from "13 files would be reformatted, 5 files would be left unchanged" to "18 files would be left unchanged"; `gdlint` goes from "Failure: 25 problems found" (defaults) to exit 0 with the kit config; the client CI shows a `godot / lint` job that fails on an unformatted `.gd`.

## Why

- assessment §5.1 (Godot row): the market baseline is `gdlint`/`gdformat --check` with gdtoolkit 4.x in CI; the kit has "no lint" and is marked "behind" with N2.
- assessment §7 item N2: gdtoolkit with a default `gdlintrc`, a fixed version, a job in `ci-godot.yml`, and an evaluation of `godot-guard` (Godot 3 syntax and invented APIs).
- Measured on stratics-client (18 `.gd` files outside `addons/`, 236 inside): gdtoolkit 4.5.0 defaults report 25 problems (20 `max-line-length` at 100, 3 `max-returns` over 6 in validators such as `autoload/network.gd:216 _validate_envelope`, 2 `class-definitions-order` in `ui/account/register_screen.gd:10` and `ui/character/character_create.gd:13`); 13 of 18 files are not gdformat-clean (250 changed lines, for example `autoload/session.gd` `signal session_started()` to `signal session_started`). After `gdformat` plus the kit config only the 2 ordering findings remain.
- The kit's own CI template never mentions formatting: `grep -rn -i 'gdlint\|gdformat\|gdtoolkit' platforms plugins` returns 0 lines in the kit today.
- `godot-guard` (brocolriri, MIT, pure Python 3.8+ stdlib, 92 rules, "Verified on Godot 4.7.2") run over stratics-client reports 2 findings, both false positives: gdUnit4 fluent chains continued on a `\` line starting with `.is_equal(` are read as the Godot 3 `._ready()` call (`tests/account/register_flow_test.gd:161` and `:163`). Decision recorded below.

## Current state

Kit, `platforms/kits/godot/README.md:5-13` (the folder index; the validator requires every non-dot file to appear in it):

```
platforms/kits/godot/README.md:7: | `.gitignore` | copy to the project root |
platforms/kits/godot/README.md:11: | `../github/workflows/ci-godot.yml` | headless CI (import + GUT + manual export) |
```

Kit, `platforms/kits/github/workflows/ci-godot.yml:11-18` (P1-05 edits lines 17-25; this prompt only adds a job):

```
platforms/kits/github/workflows/ci-godot.yml:11: jobs:
platforms/kits/github/workflows/ci-godot.yml:12:   import-and-test:
platforms/kits/github/workflows/ci-godot.yml:13:     runs-on: ubuntu-latest
platforms/kits/github/workflows/ci-godot.yml:14:     container: barichello/godot-ci:4.7.2
```

Kit, `platforms/kits/github/README.md:19`: "`ci-godot.yml` uses `barichello/godot-ci:4.7.2` (tag verified on Docker Hub on 2026-09-29). GUT tests only run if `addons/gut` exists. ..."

Kit, `plugins/dev-godot/skills/godot-standards/SKILL.md:43-45` (47 lines today):

```
plugins/dev-godot/skills/godot-standards/SKILL.md:43: ## 5. Verify
plugins/dev-godot/skills/godot-standards/SKILL.md:45: Run `godot --path . --headless --quit` and the project test command. Treat parser/import errors as failures and report the literal output.
```

Kit (new file): `platforms/kits/godot/gdlintrc`, listed in `platforms/kits/godot/README.md`. Kit (new file): `platforms/kits/godot/requirements-gdtoolkit.txt`, listed in the same README.

stratics-docs, `.github/workflows/reusable-ci-godot.yml:64-69` (the client calls this file: `stratics-client/.github/workflows/ci.yml:15: uses: ChristianPrzybulinski/stratics-docs/.github/workflows/reusable-ci-godot.yml@main`):

```
.github/workflows/reusable-ci-godot.yml:64:   import-and-test:
.github/workflows/reusable-ci-godot.yml:65:     needs: changes
.github/workflows/reusable-ci-godot.yml:66:     if: needs.changes.outputs.code == 'true'
.github/workflows/reusable-ci-godot.yml:67:     runs-on: ubuntu-latest
```

stratics-client, `AGENTS.md:30-33` (Commands block): `godot --path . --headless --quit`, `godot --path . --headless -s addons/gdUnit4/bin/GdUnitCmdTool.gd`, export. No `.gdlintrc`, no `gdlintrc`, no `requirements-gdtoolkit.txt` exist in the client (`ls -a` verified).

## Change

1. Kit (new file) `platforms/kits/godot/gdlintrc`. gdlint merges this file over its defaults (verified: with only `max-line-length` set, `class-definitions-order` still fires), so list overrides only:

```yaml
# gdlint config (gdtoolkit 4.x). Copy to the project root as `.gdlintrc`.
# Only overrides are listed; every other rule keeps the gdlint default
# (snake_case functions/variables, PascalCase classes, UPPER_CASE constants,
# Godot style-guide definition order: signals, enums, consts, exports, vars).
max-line-length: 120
# Validators with guard clauses (one return per rejected field) exceed the default 6.
max-returns: 10
```

2. Kit (new file) `platforms/kits/godot/requirements-gdtoolkit.txt`, one line: `gdtoolkit==4.5.0` (PyPI release 2025-10-09, latest 4.x on 2026-10-06; the 4.x line targets Godot 4 parsing). Add a comment line above it: `# Copy to the project root; CI and the P2-07 hook install from this file.`

3. Kit `platforms/kits/github/workflows/ci-godot.yml`: append this job after `import-and-test` (do not edit that job; P1-05 owns it). The job runs outside the Godot container because the image has no pinned Python; `find` excludes `addons/` and `.godot/` because gdformat has no exclusion option:

```yaml
  lint:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: '3.12'
      - run: pip install -r requirements-gdtoolkit.txt
      - name: gdformat --check and gdlint (project scripts; addons/ and .godot/ excluded)
        shell: bash
        run: |
          set -euo pipefail
          find . -name '*.gd' -not -path './addons/*' -not -path './.godot/*' -print0 > scripts.lst
          test -s scripts.lst
          xargs -0 gdformat --check < scripts.lst
          xargs -0 gdlint < scripts.lst
```

   Verify `actions/setup-python@v7` against github.com/actions/setup-python releases before relying on it (its README cites `@v7` on 2026-10-06).

4. Kit `platforms/kits/godot/README.md`: add rows `| \`gdlintrc\` | copy to the project root as \`.gdlintrc\` (gdlint overrides only) |` and `| \`requirements-gdtoolkit.txt\` | copy to the project root; \`pip install -r requirements-gdtoolkit.txt\` gives \`gdformat\`/\`gdlint\` 4.5.0 |`; change the `ci-godot.yml` row text to `headless CI (import + tests + gdformat/gdlint + manual export)`. Kit `platforms/kits/github/README.md:19`: append the sentence `The \`lint\` job needs \`requirements-gdtoolkit.txt\` and \`.gdlintrc\` at the project root (from \`platforms/kits/godot/\`).`

5. Kit `plugins/dev-godot/skills/godot-standards/SKILL.md` §5: after line 45 add one line: `Before pushing, run \`gdformat --check\` and \`gdlint\` over every \`.gd\` outside \`addons/\` (config: \`.gdlintrc\` from the kit; CI job \`lint\` in \`ci-godot.yml\`); fix formatting with \`gdformat <file>\`, never by hand.` Keep the file at 80 lines or fewer and do not change the frontmatter.

6. godot-guard decision (3 lines, kit). If P3-01 is merged, add to `plugins/dev-godot/skills/godot-standards/references/gdscript-4-pitfalls.md` (stay within 60 lines); otherwise add the same lines to SKILL.md §5. Text: `godot-guard (github.com/brocolriri/godot-guard, MIT, scripts/api_guard.py): evaluated 2026-10-06, not a gate. Free CLI scans for Godot 3 idioms (92 rules) but flags gdUnit4 fluent chains continued on a line starting with "." as the Godot 3 "._ready()" call (2 false positives, 0 true findings on stratics-client); blocking hooks are a paid tier. Use it manually on suspicious generated code; gdlint plus the import proof (P1-06) are the gates.`

7. Kit `CHANGELOG.md`: a `### Added` bullet under `## [Unreleased]` (proposed text in Report back).

8. stratics-client PR 1 (config, no formatting): copy `gdlintrc` to `.gdlintrc` and `requirements-gdtoolkit.txt` to the root; in `AGENTS.md` Commands block add `pip install -r requirements-gdtoolkit.txt && gdformat --check $(git ls-files '*.gd' | grep -v '^addons/') && gdlint $(git ls-files '*.gd' | grep -v '^addons/')   # style gate (CI job lint)`. No `CHANGELOG.md` edit (client PR template, DPRO-011).

9. stratics-client PR 2 (baseline, separate PR, no behavior change): run `gdformat $(git ls-files '*.gd' | grep -v '^addons/')` (13 files change); move `enum Step` above the `const` block in `ui/account/register_screen.gd` (lines 7-10) and `ui/character/character_create.gd` (lines 8-13) so `class-definitions-order` passes (Godot style guide order: enums before constants); run `gdlint` until exit 0. Diff touches only `*.gd`.

10. stratics-docs PR: add a `lint` job to `.github/workflows/reusable-ci-godot.yml` after `changes`, identical to step 3 plus `needs: changes`, `if: needs.changes.outputs.code == 'true'` and `with: lfs: false` on checkout (LFS is irrelevant to `.gd`). Add `changelog.d/p3-02-godot-lint.added.md` with one `- [FACT] ...` bullet. Merge order: client PR 1, client PR 2, docs PR (the client calls `@main`, so the job only appears once the docs PR merges; dispatch `gh workflow run ci.yml -R ChristianPrzybulinski/stratics-client` as the final proof).

## Out of scope

- The PostToolUse format hook for `*.gd` (and Java, spec): P2-07. Do not add hooks or touch `plugins/*/hooks`; the hooks validator accepts only PreToolUse today.
- `import-and-test` in `ci-godot.yml` (gdUnit4 by default, no silent skip): P1-05. The boot proof (`--import` plus `SCRIPT ERROR` grep) in SKILL.md §5 line 45: P1-06. Do not rewrite that line; add after it.
- The Godot references including `gdscript-4-pitfalls.md`: P3-01 (this prompt only appends the godot-guard note).
- `.uid` and generated-file rules: P3-01 (`scenes-and-generated-files.md`).
- Vendoring `.gdlintrc` and `requirements-gdtoolkit.txt` through `sync-project.sh`: P2-04 (today `grep -n godot platforms/tools/sync-project.sh` prints nothing; copy by hand in this task).
- stratics-server: untouched.

## Acceptance criteria

- [ ] Kit: `ls platforms/kits/godot/gdlintrc platforms/kits/godot/requirements-gdtoolkit.txt` lists both; `grep -c 'gdtoolkit==4.5.0' platforms/kits/godot/requirements-gdtoolkit.txt` prints `1`; `grep -c 'max-line-length: 120' platforms/kits/godot/gdlintrc` prints `1`.
- [ ] Kit: `grep -c '  lint:' platforms/kits/github/workflows/ci-godot.yml` prints `1`; `grep -c 'gdformat --check' platforms/kits/github/workflows/ci-godot.yml` prints `1`; `python3 -c "import yaml,sys; yaml.safe_load(open('platforms/kits/github/workflows/ci-godot.yml'))"` exits 0.
- [ ] Kit: `grep -c 'gdlintrc\|requirements-gdtoolkit.txt' platforms/kits/godot/README.md` prints `2` or more; `wc -l plugins/dev-godot/skills/godot-standards/SKILL.md` prints 80 or less; `grep -c 'gdformat --check' plugins/dev-godot/skills/godot-standards/SKILL.md` prints `1`; `grep -c 'godot-guard' plugins/dev-godot/skills/godot-standards/SKILL.md plugins/dev-godot/skills/godot-standards/references/gdscript-4-pitfalls.md 2>/dev/null` shows exactly one file with `1`.
- [ ] Kit gates: `platforms/tools/check.sh` exits 0; `platforms/tools/smoke.sh` exits 0; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` reports `OK`; `python3 platforms/ci/validations/check_kit.py --links` exits 0.
- [ ] Kit: `grep -n 'P3-02\|gdtoolkit' CHANGELOG.md` finds the new bullet above `## [10.1.0]`; `git diff --stat main` lists only the 7 kit files named in Change 1-7 (6 when the godot-guard note lands in SKILL.md).
- [ ] stratics-client, after PR 2 with the venv active (`python3 -m venv .venv && .venv/bin/pip install -r requirements-gdtoolkit.txt`): `gdformat --check $(git ls-files '*.gd' | grep -v '^addons/')` prints `18 files would be left unchanged.` and exits 0; `gdlint $(git ls-files '*.gd' | grep -v '^addons/')` exits 0; `gdformat --check` run twice gives the same result (idempotent).
- [ ] stratics-client proof: `godot --headless --path . --import` exits 0, then `godot --headless --path . -s addons/gdUnit4/bin/GdUnitCmdTool.gd -a res://tests -c --ignoreHeadlessMode | tee gdunit.log` and `sed 's/\x1b\[[0-9;]*m//g' gdunit.log | grep -Eq 'Overall Summary: [1-9][0-9]* test cases'` exit 0 with the same case count before and after PR 2 (quote both numbers in the PR body). `git diff --stat main` of PR 2 lists only `*.gd` files (13 files; the 2 reordered files are among the 13 gdformat rewrites).
- [ ] stratics-docs: `python3 .github/spec-lint/check_spec.py docs/spec .github/spec-lint/schemas` exits 0; `python3 tools/spec-trace/spec_trace.py check` exits 0; `ls changelog.d/p3-02-godot-lint.added.md` exists; the PR body `proof` block uses only first words from `ops/review-loop/config.json` `proof_allowlist` (`python3`, `grep`, `test`, `godot` are allowed; `gdformat`, `gdlint` and `pip` are not): prove with `grep -c '  lint:' .github/workflows/reusable-ci-godot.yml`. In the client PRs use the module forms, verified with gdtoolkit 4.5.0: `python3 -m gdtoolkit.formatter --check <files>` and `python3 -m gdtoolkit.linter <files>`.
- [ ] Final: `gh run list -R ChristianPrzybulinski/stratics-client --workflow ci.yml -L 1` shows a run whose `lint` job concluded `success` after the docs PR merged.

## Conventions

- Everything committed is in English; plain ASCII punctuation in new text.
- No layout or path change (10.x layout frozen by P1-01): `platforms/kits/godot/`, `platforms/kits/github/workflows/` and `plugins/dev-godot/` keep their paths. `VERSION` untouched.
- `CHANGELOG.md` gets a `## [Unreleased]` `### Added` bullet with what, why and proof (measured numbers above).
- `README.md` of every touched kit folder lists every entry by name (`platforms/kits/godot/README.md`; a folder never has both INDEX.md and README.md). Backtick paths ending in `.md`, `.sh`, `.json`, `.yml` or `.yaml` in kit markdown must resolve (`check_kit.py` backtick check); keep the existing `../github/workflows/ci-godot.yml` row as is.
- SKILL.md at 80 lines or fewer; the skill description is unchanged (budget 6,803 of 7,200 chars stays). If the godot-guard note goes into `gdscript-4-pitfalls.md`, that reference stays at 60 lines or fewer with its P3-01 frontmatter untouched.
- No new hook: the hooks validator accepts only PreToolUse (P2-07 owns PostToolUse).
- Conventional Commits with `Refs: P3-02` (kit) and `Refs: P3-02, DTEC-010` (stratics); PR body = What / Why / How I tested (literal output) / Refs; stratics PRs also fill the `proof` block; stratics-docs adds the `changelog.d` fragment; stratics-client never edits `CHANGELOG.md` directly.
- Gates: kit = `platforms/tools/check.sh`, `platforms/tools/smoke.sh`, the unittest discover, `check_kit.py --links`; stratics-docs = `check_spec.py` and `spec_trace.py check`; stratics-client = `godot --headless --path . --import` then the gdUnit4 run.
- The executor may be Devin or Claude Code; nothing here is Claude-specific.

## Report back

Final message format:

- done: each created or edited path per repo with the lines changed; each PR URL in merge order; every gate and acceptance command with its literal output (the gdformat summary line, the gdlint exit code, the two `Overall Summary` counts, the `lint` job conclusion).
- unverified: anything not reproduced (for example `actions/setup-python@v7` if the release page was unreachable, or the client `lint` job if the docs PR was not merged yet), and whether `godot / lint` was added to the client's required checks (needs repo admin; say if it was not).
- next step: P2-07 wires the same `requirements-gdtoolkit.txt` into the PostToolUse hook; P2-04 copies `.gdlintrc` and the requirements file through `sync-project.sh`; P3-01 owns the pitfalls reference if the godot-guard note had to land in SKILL.md.
- Proposed CHANGELOG line (under `### Added`):
  `- Godot CI kit: gdtoolkit 4.5.0 pinned in platforms/kits/godot/requirements-gdtoolkit.txt, a default gdlintrc (max-line-length 120, max-returns 10, gdlint defaults otherwise) and a lint job (gdformat --check plus gdlint, addons/ and .godot/ excluded) in ci-godot.yml; godot-standards §5 names the command; godot-guard evaluated and not adopted as a gate (2 false positives, 0 true findings on stratics-client). Evidence: stratics-client went from 13 of 18 scripts unformatted and 25 gdlint problems to 0 after the baseline (P3-02, assessment §5.1 and §7 N2).`
