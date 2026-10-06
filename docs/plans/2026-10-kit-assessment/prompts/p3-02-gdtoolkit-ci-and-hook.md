# P3-02 — gdtoolkit lint and format in the Godot CI kit and in stratics-client

Phase: 3 · Repos: kit, stratics-client, stratics-docs · Branch to create: feat/p3-02-gdtoolkit-ci from main (kit and stratics-docs: `feat/p3-02-gdtoolkit-ci`; stratics-client PR 1: `feat/p3-02-gdtoolkit-ci`; stratics-client PR 2: `chore/p3-02-gdformat-baseline`, branched from main after PR 1 is merged) · Depends on: P1-05 (P1-06 is not required: Change 5 works with or without it) · Effort: ~4 h

## Goal

The Godot CI kit and the Stratics client gain a deterministic style gate: `gdformat --check` and `gdlint` (gdtoolkit 4.5.0, pinned) run in CI over every project script outside `addons/` and `.godot/`, with one `gdlintrc` shipped by the kit and copied to the project. stratics-client gets a one-time formatting baseline so the gate starts green. Measurable result: `gdformat --check` on stratics-client goes from "13 files would be reformatted, 5 files would be left unchanged" to "18 files would be left unchanged"; `gdlint` goes from "Failure: 25 problems found" (defaults) to exit 0 with the kit config; the client CI shows a `godot / lint` job that fails on an unformatted `.gd`.

## Why

- assessment §5.1 (Godot row): the market baseline is `gdlint`/`gdformat --check` with gdtoolkit 4.x in CI; the kit has "no lint" and is marked "behind" with N2.
- assessment §7 item N2: gdtoolkit with a default `gdlintrc`, a fixed version, a job in `ci-godot.yml`, and an evaluation of `godot-guard` (Godot 3 syntax and invented APIs).
- Measured on stratics-client (18 `.gd` files outside `addons/`, 236 inside): gdtoolkit 4.5.0 defaults report 25 problems (20 `max-line-length` at 100, 3 `max-returns` over 6 in validators such as `autoload/network.gd:216 _validate_envelope`, 2 `class-definitions-order` in `ui/account/register_screen.gd:10` and `ui/character/character_create.gd:13`); 13 of 18 files are not gdformat-clean (250 changed lines, for example `autoload/session.gd` `signal session_started()` to `signal session_started`). After `gdformat` plus the kit config only the 2 ordering findings remain.
- The kit's own CI template never mentions formatting: `grep -rn -i 'gdlint\|gdformat\|gdtoolkit' platforms plugins` returns 0 lines in the kit today.
- `godot-guard` (brocolriri, MIT, pure Python 3.8+ stdlib, 92 rules, "Verified on Godot 4.7.2") run over stratics-client reports 2 findings, both false positives: gdUnit4 fluent chains continued on a `\` line starting with `.is_equal(` are read as the Godot 3 `._ready()` call (`tests/account/register_flow_test.gd:161` and `:163`). Decision recorded below.

## Current state

Kit, `platforms/kits/godot/README.md:5-13` (the folder index; the validator requires every non-dot file to appear in it; text on main before P1-05; after P1-05 the `ci-godot.yml` cell reads as P1-05 step 6 specifies):

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

Kit, `platforms/kits/github/README.md:19` (text on main before P1-05; after P1-05 the second sentence reads as P1-05 step 7 specifies): "`ci-godot.yml` uses `barichello/godot-ci:4.7.2` (tag verified on Docker Hub on 2026-09-29). GUT tests only run if `addons/gut` exists. ..."

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

2. Kit (new file) `platforms/kits/godot/requirements-gdtoolkit.txt`, one line: `gdtoolkit==4.5.0` (PyPI release 2025-10-09, latest 4.x on 2026-10-06; the 4.x line targets Godot 4 parsing). Add a comment line above it: `# Copy to the project root; the CI lint job installs from this file; the P2-07 hook uses the gdtoolkit on PATH; Devin environments add pip install -r requirements-gdtoolkit.txt to the Godot environment setup.`

3. Kit `platforms/kits/github/workflows/ci-godot.yml`: insert this job between `import-and-test` and `export` (after the `export` job is also acceptable); leave both existing jobs byte-identical (P1-05 owns `import-and-test`). The job runs outside the Godot container because the image has no pinned Python; `find` excludes `addons/` and `.godot/` because gdformat has no CLI exclusion flag (only an `excluded_directories` key in `gdformatrc`, which this kit does not ship):

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

4. Kit `platforms/kits/godot/README.md`: add rows `| \`gdlintrc\` | copy to the project root as \`.gdlintrc\` (gdlint overrides only) |` and `| \`requirements-gdtoolkit.txt\` | copy to the project root; \`pip install -r requirements-gdtoolkit.txt\` gives \`gdformat\`/\`gdlint\` 4.5.0 |`; in the `../github/workflows/ci-godot.yml` row, insert ` + gdformat/gdlint` (or `, gdformat/gdlint,` in P1-05's comma form) immediately before `manual export`; keep every other word P1-05 left in the cell. Kit `platforms/kits/github/README.md:19`: append the sentence `The \`lint\` job needs \`requirements-gdtoolkit.txt\` and \`.gdlintrc\` at the project root (from \`platforms/kits/godot/\`).`

5. Kit `plugins/dev-godot/skills/godot-standards/SKILL.md` §5: insert one line as the last paragraph of `## 5. Verify`, immediately before the blank line that precedes `Done when:` (line 46 on main today; one line later if P1-06 is merged). Do not touch the lines P1-06 wrote. The line: `Before pushing, run \`gdformat --check\` and \`gdlint\` over every \`.gd\` outside \`addons/\` (config: \`.gdlintrc\` from the kit; CI job \`lint\` in \`ci-godot.yml\`); fix formatting with \`gdformat <file>\`, never by hand.` Keep the file at 80 lines or fewer and do not change the frontmatter.

6. godot-guard decision (kit): one paragraph on one physical line (the word `godot-guard` must occur on exactly one line of the file, for the acceptance count). If P3-01 is merged, add it as the last paragraph of `plugins/dev-godot/skills/godot-standards/references/gdscript-4-pitfalls.md` (stay within 60 lines); otherwise insert the same line in SKILL.md §5 immediately after the Change 5 line (before the blank line that precedes `Done when:`). Text: `godot-guard (github.com/brocolriri/godot-guard, MIT, scripts/api_guard.py): evaluated 2026-10-06, not a gate. Free CLI scans for Godot 3 idioms (92 rules) but flags gdUnit4 fluent chains continued on a line starting with "." as the Godot 3 "._ready()" call (2 false positives, 0 true findings on stratics-client); blocking hooks are a paid tier. Use it manually on suspicious generated code; gdlint plus the import proof (P1-06) are the gates.`

7. Kit `CHANGELOG.md`: a `### Added` bullet under `## [Unreleased]` (proposed text in Report back).

8. stratics-client PR 1 (config, no formatting): copy `gdlintrc` to `.gdlintrc` and `requirements-gdtoolkit.txt` to the root; in `AGENTS.md` Commands block add `pip install -r requirements-gdtoolkit.txt && gdformat --check $(git ls-files '*.gd' | grep -v '^addons/') && gdlint $(git ls-files '*.gd' | grep -v '^addons/')   # style gate (CI job lint)`. No `CHANGELOG.md` edit (client PR template, DPRO-011).

9. stratics-client PR 2 (baseline, separate PR, no behavior change, branch `chore/p3-02-gdformat-baseline` from main after PR 1 merges): first move `enum Step` above the `const` block in `ui/account/register_screen.gd` (const block lines 7-8, enum on line 10) and `ui/character/character_create.gd` (const block lines 7-11, enum on line 13) so `class-definitions-order` passes (Godot style guide order: enums before constants); then run `gdformat $(git ls-files '*.gd' | grep -v '^addons/')` (13 files change, the 2 reordered files among them); then `gdlint $(git ls-files '*.gd' | grep -v '^addons/')` until exit 0 and `gdformat --check` until clean. Diff touches only `*.gd`.

10. stratics-docs PR: add a `lint` job to `.github/workflows/reusable-ci-godot.yml` after `changes`, identical to step 3 plus `needs: changes`, `if: needs.changes.outputs.code == 'true'` and `with: lfs: false` on checkout (LFS is irrelevant to `.gd`). Add `changelog.d/p3-02-gdtoolkit-ci.added.md` (branch slug, per `changelog.d/README.md`; use the issue number instead if one is created) with one `- [FACT] ...` bullet. Merge order: client PR 1, client PR 2, docs PR (the client calls `@main`, so the job only appears once the docs PR merges; dispatch `gh workflow run ci.yml -R ChristianPrzybulinski/stratics-client` as the final proof).

## Out of scope

- The PostToolUse format hook for `*.gd` (and Java, spec): P2-07. Do not add hooks or touch `plugins/*/hooks` (P2-07 owns PostToolUse; the PreToolUse-only validator rule changes there).
- `import-and-test` in `ci-godot.yml` (gdUnit4 by default, no silent skip): P1-05. The boot proof (`--import` plus `SCRIPT ERROR` grep) in SKILL.md §5 line 45: P1-06. Do not rewrite that paragraph; add after it (anchor in Change 5).
- The Godot references including `gdscript-4-pitfalls.md`: P3-01 (this prompt only appends the godot-guard note).
- `.uid` and generated-file rules: P3-01 (`scenes-and-generated-files.md`).
- Vendoring `.gdlintrc` and `requirements-gdtoolkit.txt` through `sync-project.sh`: no prompt covers it (P2-04 only generates `CLAUDE.md` and `.claude/settings.json` per profile; today `grep -n godot platforms/tools/sync-project.sh` prints nothing); copy by hand in this task and report the follow-up.
- stratics-server: untouched.

## Acceptance criteria

- [ ] Kit: `ls platforms/kits/godot/gdlintrc platforms/kits/godot/requirements-gdtoolkit.txt` lists both; `grep -c 'gdtoolkit==4.5.0' platforms/kits/godot/requirements-gdtoolkit.txt` prints `1`; `grep -c 'max-line-length: 120' platforms/kits/godot/gdlintrc` prints `1`.
- [ ] Kit: `grep -c '  lint:' platforms/kits/github/workflows/ci-godot.yml` prints `1`; `grep -c 'gdformat --check' platforms/kits/github/workflows/ci-godot.yml` prints `2` (the step name and the run line); `python3 -c "import yaml,sys; yaml.safe_load(open('platforms/kits/github/workflows/ci-godot.yml'))"` exits 0. Local negative proof of the gate (gdtoolkit 4.5.0 on PATH): `printf 'func f( ):\n\tpass\n' > /tmp/bad.gd; ! gdformat --check /tmp/bad.gd` exits 0 (an unformatted `.gd` makes `gdformat --check` fail).
- [ ] Kit: `grep -c 'gdlintrc\|requirements-gdtoolkit.txt' platforms/kits/godot/README.md` prints `2` or more; `wc -l plugins/dev-godot/skills/godot-standards/SKILL.md` prints 80 or less; `grep -c 'gdformat --check' plugins/dev-godot/skills/godot-standards/SKILL.md` prints `1`; `grep -c 'godot-guard' plugins/dev-godot/skills/godot-standards/SKILL.md plugins/dev-godot/skills/godot-standards/references/gdscript-4-pitfalls.md 2>/dev/null` shows exactly one file with `1`.
- [ ] Kit gates: `platforms/tools/check.sh` exits 0; `platforms/tools/smoke.sh` exits 0; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` reports `OK`; `python3 platforms/ci/validations/check_kit.py --links` exits 0. If `check_kit.py` (and therefore `check.sh`) fails only on `docs/plans/...` links from other prompts (pre-existing on the branch today: p2-09, p2-10, p3-09 and others), record it under unverified as pre-existing; the files named in Change 1-7 must produce no `FAIL` line.
- [ ] Kit: `grep -n 'P3-02\|gdtoolkit' CHANGELOG.md` finds the new bullet above `## [10.1.0]`; `git diff --stat main` lists only the kit files named in Change 1-7: 7 files when the godot-guard note lands in SKILL.md, 8 when it lands in `references/gdscript-4-pitfalls.md`.
- [ ] stratics-client, after PR 2 with a venv created outside the repository active (`python3 -m venv ../gdtoolkit-venv && ../gdtoolkit-venv/bin/pip install -r requirements-gdtoolkit.txt`; `.gitignore` has no `.venv` entry, so `git status --porcelain` must list no venv before committing): `gdformat --check $(git ls-files '*.gd' | grep -v '^addons/')` prints `18 files would be left unchanged` (no trailing period; only the mixed summary has one) and exits 0; `gdlint $(git ls-files '*.gd' | grep -v '^addons/')` exits 0; `gdformat --check` run twice gives the same result (idempotent).
- [ ] stratics-client proof: `godot --headless --path . --import` exits 0, then `godot --headless --path . -s addons/gdUnit4/bin/GdUnitCmdTool.gd -a res://tests -c --ignoreHeadlessMode | tee gdunit.log` and `sed 's/\x1b\[[0-9;]*m//g' gdunit.log | grep -Eq 'Overall Summary: [1-9][0-9]* test cases'` exit 0 with the same case count before and after PR 2 (quote both numbers in the PR body). `git diff --stat main` of PR 2 lists only `*.gd` files (13 files; the 2 reordered files are among the 13 gdformat rewrites).
- [ ] stratics-docs: `python3 .github/spec-lint/check_spec.py docs/spec .github/spec-lint/schemas` exits 0; `python3 tools/spec-trace/spec_trace.py check` exits 0; `ls changelog.d/p3-02-gdtoolkit-ci.added.md` exists; the PR body `proof` block uses only first words from `ops/review-loop/config.json` `proof_allowlist` (`python3`, `grep`, `test`, `godot` are allowed; `gdformat`, `gdlint` and `pip` are not), and the loop's `command_allowed` (`ops/review-loop/loop.py`) refuses `$(`, backticks and the word `exec`, so neither `$(git ls-files ...)` nor `find -exec` may appear in a proof block: prove with `grep -c '  lint:' .github/workflows/reusable-ci-godot.yml`. Client PR 2 proof block: these literal module-form lines (gdformat and gdlint accept directories; `autoload scenes tests ui` are the top-level directories holding the 18 scripts outside `addons/`, from `git ls-files '*.gd' | grep -v '^addons/' | cut -d/ -f1 | sort -u`; verified with gdtoolkit 4.5.0: 13/5 files and the gdlint problems before the baseline): `python3 -m gdtoolkit.formatter --check autoload scenes tests ui` and `python3 -m gdtoolkit.linter autoload scenes tests ui`. Client PR 1 proof block (config only, scripts still unformatted: with the kit rc and before gdformat, `gdlint` still reports `Failure: 5 problems found` and `gdformat --check` reports 13 files, both exit 1, so the module-form lines would make the loop reject PR 1): `test -f .gdlintrc`, `grep -c 'gdtoolkit==4.5.0' requirements-gdtoolkit.txt` and `grep -c 'gdformat --check' AGENTS.md`.
- [ ] Final, after the docs PR merged (`gh run list` prints runs, not jobs, so read the job through `gh run view`): `id=$(gh run list -R ChristianPrzybulinski/stratics-client --workflow ci.yml -L 1 --json databaseId -q '.[0].databaseId')` then `gh run view "$id" -R ChristianPrzybulinski/stratics-client --json jobs -q '.jobs[] | select(.name == "godot / lint") | .conclusion'` prints `success`.

## Conventions

- Everything committed is in English; plain ASCII punctuation in new text (`§` allowed in `CHANGELOG.md` only, as in the existing entries).
- No layout or path change (10.x layout frozen by P1-01): `platforms/kits/godot/`, `platforms/kits/github/workflows/` and `plugins/dev-godot/` keep their paths. `VERSION` untouched.
- `CHANGELOG.md` gets a `## [Unreleased]` `### Added` bullet with what, why and proof (measured numbers above).
- `README.md` of every touched kit folder lists every entry by name (`platforms/kits/godot/README.md`; a folder never has both INDEX.md and README.md). Backtick paths ending in `.md`, `.sh`, `.json`, `.yml` or `.yaml` in kit markdown must resolve (`check_kit.py` backtick check); keep the existing `../github/workflows/ci-godot.yml` row as is.
- SKILL.md at 80 lines or fewer; the skill description is unchanged (budget 6,803 of 7,200 chars stays). If the godot-guard note goes into `gdscript-4-pitfalls.md`, that reference stays at 60 lines or fewer with its P3-01 frontmatter untouched.
- No new hook: do not add hooks (P2-07 owns PostToolUse; the PreToolUse-only validator rule changes there).
- Conventional Commits with `Refs: P3-02` (kit) and `Refs: P3-02, DTEC-010` (stratics); PR body = What / Why / How I tested (literal output) / Refs; stratics PRs also fill the `proof` block; stratics-docs adds the `changelog.d` fragment; stratics-client never edits `CHANGELOG.md` directly.
- Gates: kit = `platforms/tools/check.sh`, `platforms/tools/smoke.sh`, the unittest discover, `check_kit.py --links`; stratics-docs = `check_spec.py` and `spec_trace.py check`; stratics-client = `godot --headless --path . --import` then the gdUnit4 run.
- The executor may be Devin or Claude Code; nothing here is Claude-specific.

## Report back

Final message format:

- done: each created or edited path per repo with the lines changed; each PR URL in merge order; every gate and acceptance command with its literal output (the gdformat summary line, the gdlint exit code, the two `Overall Summary` counts, the `lint` job conclusion).
- unverified: anything not reproduced (for example `actions/setup-python@v7` if the release page was unreachable, or the client `lint` job if the docs PR was not merged yet), whether `godot / lint` was added to the client's required checks (needs repo admin; say if it was not), and that the client proof lines depend on the review-loop machine having gdtoolkit 4.5.0 importable by `python3` (owner one-time `python3 -m pip install -r requirements-gdtoolkit.txt` or a venv on PATH; `proof_env` in `config.json` only sets `JAVA_HOME` for the server); say so in the PR body.
- next step: no prompt owns the Devin install (P3-03 names P3-02 for gdtoolkit in the Godot environment); report it as a follow-up for the Godot environment file (`pip install -r requirements-gdtoolkit.txt` in its setup); follow-up: extend the `godot` profile of `sync-project.sh` (P2-04 shape) to copy `gdlintrc` as `.gdlintrc` and `requirements-gdtoolkit.txt`; P3-01 owns the pitfalls reference if the godot-guard note had to land in SKILL.md.
- Proposed CHANGELOG line (under `### Added`):
  `- Godot CI kit: gdtoolkit 4.5.0 pinned in platforms/kits/godot/requirements-gdtoolkit.txt, a default gdlintrc (max-line-length 120, max-returns 10, gdlint defaults otherwise) and a lint job (gdformat --check plus gdlint, addons/ and .godot/ excluded) in ci-godot.yml; godot-standards §5 names the command; godot-guard evaluated and not adopted as a gate (2 false positives, 0 true findings on stratics-client). Evidence: stratics-client went from 13 of 18 scripts unformatted and 25 gdlint problems to 0 after the baseline (P3-02, assessment §5.1 and §7 N2).`
