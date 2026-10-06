# P1-05 — Godot tests: gdUnit4 by default, CI never skips silently, GDScript test policy

Phase: 1 · Repos: kit · Branch to create: fix/p1-05-godot-tests-gdunit4-never-skip from main (the `docs/plans/` folder is not on main yet: the Refs path in Conventions exists once the plan is merged; until then cite the kit commit SHA that carries the plan) · Depends on: none (coordinate `ci-godot.yml` with P1-06, see Change step 1) · Effort: ~3 h

## Goal

Make the kit's Godot CI template a gate that can fail: `platforms/kits/github/workflows/ci-godot.yml` runs gdUnit4 by default, GUT as the alternative, fails when neither runner exists or when zero tests execute, and uploads the test report as a workflow artifact. Align the three documents that still name GUT as the only runner (`project-agents-godot-2d.md`, `platforms/kits/godot/README.md`, `platforms/kits/github/README.md`) and `godot-standards`, which names no runner today, and give `testing` a GDScript policy: no percentage gate, every game rule in a pure `RefCounted` class tested without a `SceneTree`. Measurable result: `grep -c 'skipping tests' platforms/kits/github/workflows/ci-godot.yml` prints `0`; the step run against a checkout without `addons/gdUnit4` and `addons/gut` exits 1; both `SKILL.md` files stay at or under 80 lines and keep their descriptions, so the plugin `INDEX.md` files and the description budget do not move.

## Why

- assessment §4.4 (Tests): the kit and `ci-godot.yml` assume GUT; the project uses gdUnit4 (stratics-docs DTEC-010). The kit's CI template skips the tests silently when `addons/gut` is absent ("skipping tests") and exits green: exactly the "gate that cannot fail" that the same kit's `reviewer` forbids.
- assessment §4.4 (Coverage): `testing` requires 100% line/branch plus mutation >= 80% (ASCII paraphrase of its `≥80%`) in the domain. That exists for Java (JaCoCo/PIT), not for GDScript (no mature mutation tooling); for the client the rule is inapplicable, and the agent either ignores it or invents numbers.
- assessment §6 item D2: gdUnit4 as the default, GUT as the alternative, never skip silently; fail when the runner is absent and require "N test cases" > 0 in the output (the project's `reusable-ci-godot.yml` already does this: promote it to the kit); emit JUnit XML for the PR; GDScript coverage policy "every game rule in a pure class tested without `SceneTree`; no numeric gate".
- kit `plugins/quality-core/agents/reviewer.md:21`: "A proof that cannot fail (zero tests, zero schemas, an empty input set) proves nothing"; kit `plugins/quality-core/skills/validate-implementation/SKILL.md:32`: "A gate that passes on empty input (zero tests, zero schemas) is not proof". The kit's own CI template violates both.
- stratics-docs `docs/spec/decisions/DTEC-010-godot-project.md:27`: "**gdUnit4** as the test framework; tests live in `tests/` and must run headless in CI"; stratics-client `AGENTS.md:8`: "CI must run the suite headless and **fail when the runner is absent** (a green CI with zero tests is a bug)"; stratics-client `addons/gdUnit4/plugin.cfg:6` `version="6.2.1"`; 9 suites under `tests/**/*_test.gd` today, all `extends GdUnitTestSuite`.
- Verified facts (2026-10-06): the gdUnit4 README version table lists Godot 4.5 to 4.7.1; GUT 9.7.1 (`godot_4_7` branch) targets 4.7.x; `barichello/godot-ci:4.7.2` exists on Docker Hub.

## Current state

- kit `platforms/kits/github/workflows/ci-godot.yml` (42 lines):
  `ci-godot.yml:17` `      - name: Project import (generates .godot/, validates resources)`
  `ci-godot.yml:18` `        run: godot --headless --path . --quit`
  `ci-godot.yml:19` `      - name: GUT tests (if addons/gut exists)`
  `ci-godot.yml:21` `          if [ -d addons/gut ]; then`
  `ci-godot.yml:22` `            godot --headless --path . -s addons/gut/gut_cmdln.gd -gexit`
  `ci-godot.yml:24` `            echo "addons/gut missing; skipping tests"`
  `ci-godot.yml:39` `      - uses: actions/upload-artifact@v7` (export job; reuse the same action version).
- stratics-docs `.github/workflows/reusable-ci-godot.yml:89-112` is the proven source: `:92` `run: godot --headless --path . --import`; `:98-101` exit 1 when `addons/gdUnit4` is missing; `:102-105` exit 1 when no `*_test.gd` exists under `tests/`; `:106-107` `godot --headless --path . -s addons/gdUnit4/bin/GdUnitCmdTool.gd -a res://tests -c --ignoreHeadlessMode | tee gdunit.log`; `:109` `grep -Eq 'Overall Summary: [1-9][0-9]* test cases'` after stripping ANSI codes; `:94-95` `shell: bash` because container jobs default to `sh -e` and dash rejects `set -o pipefail`. It writes no artifact.
- kit `plugins/dev-godot/templates/project-agents-godot-2d.md` (87 lines):
  `project-agents-godot-2d.md:8` `- Tests: [GUT | gdUnit4] in `tests/`. Renderer: [Forward+ | Mobile | Compatibility].`
  `project-agents-godot-2d.md:31` `godot --path . --headless -s addons/gut/gut_cmdln.gd   # run GUT (adjust to the framework)`
  `project-agents-godot-2d.md:77` `- Conventional Commits; PR with a GIF/screenshot when the change is visual.`
- kit `plugins/dev-godot/skills/godot-standards/SKILL.md` (47 lines; description on line 3 must not change):
  `SKILL.md:43` `## 5. Verify`
  `SKILL.md:45` `Run `godot --path . --headless --quit` and the project test command. Treat parser/import errors as failures and report the literal output.`
- kit `plugins/dev-core/skills/testing/SKILL.md` (50 lines; description on line 3 must not change):
  `SKILL.md:19` `Domain rules involving business logic, money, inventory, rewards, battle or authorization require 100% line and branch coverage plus mutation score ≥80%. These gates are never reduced.` (the `≥` is U+2265 in the file).
  `SKILL.md:50` `Done when: required domain percentages and mutation pass, every non-trivial non-domain change has one proof, integrations have happy/sad coverage, and no test sleeps or asserts implementation calls.`
- kit `platforms/kits/godot/README.md:11` `| `../github/workflows/ci-godot.yml` | headless CI (import + GUT + manual export) |`
- kit `platforms/kits/godot/.gitignore:2-3` `.godot/` and `build/`; no `reports/` entry (listed in `platforms/kits/godot/README.md:7`).
- kit `platforms/kits/github/README.md:19` `- `ci-godot.yml` uses `barichello/godot-ci:4.7.2` (tag verified on Docker Hub on 2026-09-29). GUT tests only run if `addons/gut` exists. Windows/macOS export only via `workflow_dispatch` and requires `export_presets.cfg` committed to the repo.`
- kit `CHANGELOG.md:5` `## [Unreleased]` with `### Added` and `### Changed` subsections; append the bullet at the end of `### Changed`, before `## [10.1.0]`.

## Change

1. kit `platforms/kits/github/workflows/ci-godot.yml`, job `import-and-test`: anchor by content, not by line number, because P1-06 moves these lines. Replace the step whose name is `GUT tests (if addons/gut exists)` (from its `- name:` line through its closing `fi`; lines 19-25 on main) with the `Unit tests` and `Upload test reports` steps of the block below, verbatim. If P1-06 has not merged, also replace the `Project import` step's two lines (17-18 on main) with the first two lines of the block. If P1-06 merged first, keep its `Project import` and `Boot proof` steps byte-identical and insert the two new steps after `Boot proof`. The `- uses: actions/checkout@v7` line and the `export` job stay unchanged. Coordination with P1-06: the gdUnit4 runner needs the script-class cache that only `--import` writes (stratics-docs `reusable-ci-godot.yml:90-91`, stratics-docs#84), so this task sets the import line to `--import`; P1-06 owns the `SCRIPT ERROR` grep and the export job's import line (`:34`). Whichever PR merges second rebases; the merged import line is `run: godot --headless --path . --import` either way.

```yaml
      - name: Project import (generates .godot/ and the script-class cache, validates resources)
        run: godot --headless --path . --import
      - name: Unit tests (gdUnit4 by default, GUT as the alternative; a missing runner or zero tests fails)
        # container jobs default to `sh -e`; dash rejects `set -o pipefail` (exit 2)
        shell: bash
        run: |
          set -euo pipefail
          mkdir -p reports
          if [ -d addons/gdUnit4 ]; then
            if ! find tests -name '*_test.gd' -print -quit 2>/dev/null | grep -q .; then
              echo "::error::no gdUnit4 suites (*_test.gd) under tests/; a green run with zero tests is a failure" >&2
              exit 1
            fi
            godot --headless --path . -s addons/gdUnit4/bin/GdUnitCmdTool.gd -a res://tests -c --ignoreHeadlessMode \
              | tee reports/gdunit.log
            # the runner can exit 0 having loaded nothing: require >= 1 executed test case
            if ! sed 's/\x1b\[[0-9;]*m//g' reports/gdunit.log | grep -Eq 'Overall Summary: [1-9][0-9]* test cases'; then
              echo "::error::gdUnit4 executed no test case; check the runner and the import step" >&2
              exit 1
            fi
          elif [ -d addons/gut ]; then
            if ! find tests -name 'test_*.gd' -print -quit 2>/dev/null | grep -q .; then
              echo "::error::no GUT scripts (test_*.gd) under tests/; a green run with zero tests is a failure" >&2
              exit 1
            fi
            godot --headless --path . -s addons/gut/gut_cmdln.gd -gdir=res://tests -ginclude_subdirs -gexit \
              -gjunit_xml_file=res://reports/gut-results.xml | tee reports/gut.log
            if ! grep -Eq 'tests="[1-9][0-9]*"' reports/gut-results.xml; then
              echo "::error::GUT executed no test; check the runner and the import step" >&2
              exit 1
            fi
          else
            echo "::error::neither addons/gdUnit4 nor addons/gut exists; tests must not be skipped" >&2
            exit 1
          fi
      - name: Upload test reports (JUnit XML and runner log)
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: godot-test-reports
          path: reports/
          if-no-files-found: warn
```

   gdUnit4 writes its JUnit report under `reports/report_<n>/results.xml` by default; the proof is in the vendored addon beside the kit, stratics-client `addons/gdUnit4/src/core/runners/GdUnitTestCIRunner.gd:71` ("The default is res://reports/", option `-rd` at `:340`), `addons/gdUnit4/src/GdUnitConstants.gd:10` (`REPORT_DIR_PREFIX = "report_"`) and `addons/gdUnit4/src/reporters/xml/JUnitXmlReportWriter.gd:31` (`"%s/results.xml"`), so no web check is needed for it. GUT is not checked out locally: verify against GUT `godot_4_7` `addons/gut/cli/gut_cli.gd` (`-gdir` :114, `-ginclude_subdirs` :115, `-gjunit_xml_file` :150) and `addons/gut/junit_xml_export.gd:91` (`tests=` on `<testsuites>`), or the wiki "Command Line" page (`https://github.com/bitwes/Gut/wiki`), before relying on it. Keep the gdUnit4 command identical to stratics-docs `reusable-ci-godot.yml:106` (the proven form).

2. kit `platforms/kits/godot/.gitignore`: insert `reports/` after line 3 (`build/`), with the comment `# test reports written by gdUnit4/GUT in CI` above it. The file is already listed in `platforms/kits/godot/README.md:7`.

3. kit `plugins/dev-godot/templates/project-agents-godot-2d.md`:
   a. Line 8: change only the token `[GUT | gdUnit4]` to `[gdUnit4 | GUT]` (gdUnit4 is the kit default). If P1-04 merged first, the line carries an extra "Movement model" sentence; keep it.
   b. Replace the single line containing `addons/gut/gut_cmdln.gd` (line 31 on main; 32 after P1-06, whose step 5 turns line 30 into two lines) with these two lines, gdUnit4 first, keeping the block's comment column:

```bash
godot --path . --headless -s addons/gdUnit4/bin/GdUnitCmdTool.gd -a res://tests -c --ignoreHeadlessMode   # run gdUnit4 (default)
godot --path . --headless -s addons/gut/gut_cmdln.gd -gdir=res://tests -ginclude_subdirs -gexit             # run GUT (alternative); delete the runner not used
```

   c. After line 77 (`- Conventional Commits; PR with a GIF/screenshot ...`) insert: `- CI runs the suite headless and fails when the runner is missing or zero tests execute; never skip tests to get a green run (see the kit `ci-godot.yml`).` Keep `ci-godot.yml` as a bare backtick name without a directory prefix: `check_kit.py:831-832` only resolves backtick paths that start with `../`, `./`, `references/`, `templates/`, `platforms/` or `plugins/`.
   d. Do not touch the `--headless --quit` import line (line 30 on main, P1-06), the `## Patterns` bullets about movement/collision and the `## Boundaries` list (lines 40-46 and 79-83 on main; P1-04 and P1-06, and P1-04 shifts them by inserting a `## Movement model` section before `## Git & PR`), or the `HealthComponent` example.

4. kit `plugins/dev-godot/skills/godot-standards/SKILL.md`, section 5: keep its first paragraph untouched (line 45 on main; P1-06 rewrites it into two lines, the second starting `Report the literal output of all three ...`) and insert after the last line of that paragraph, before the blank line that precedes `Done when:`, one blank line plus this paragraph, verbatim:

```markdown
Test runner: gdUnit4 by default (`-s addons/gdUnit4/bin/GdUnitCmdTool.gd -a res://tests -c --ignoreHeadlessMode`), GUT only when the project `AGENTS.md` says so (`-s addons/gut/gut_cmdln.gd -gdir=res://tests -ginclude_subdirs -gexit`). A run that executes zero tests, or a missing runner, is a failure, never a skip. Game rules live in pure `RefCounted` classes with scene-free tests; scene tests are integration only (skill `testing`, section 1).
```

   Resulting length: 47 + 2 = 49 lines (48 + 2 = 50 if P1-06 merged first; 51 + 2 = 53 if P1-04 merged first, per P1-04's own count; limit 80). Frontmatter, sections 1-4 and `Done when` stay as they are.

5. kit `plugins/dev-core/skills/testing/SKILL.md`, section 1: insert after line 21 one blank line plus this paragraph, verbatim:

```markdown
GDScript (Godot): no line, branch or mutation percentage gate; the tooling does not exist. Instead, every game rule (combat, inventory, movement validation, economy, rewards) lives in a pure `RefCounted` class with `class_name`, built with `.new()` and tested without a `SceneTree` (no `add_child`, no autoload, no `get_node`; inject the clock and the RNG). Scene tests (gdUnit4 scene runner, GUT `add_child_autofree`) are integration tests: few, around a `.tscn` contract. CI fails when the runner is absent or zero tests execute.
```

   Then edit line 50 (`Done when:`) so it starts `Done when: required domain percentages and mutation pass (JVM) or every GDScript rule has a scene-free test, every non-trivial ...` (the rest unchanged). Resulting length: 50 + 2 = 52 lines (limit 80). Frontmatter (description on line 3) and sections 2-6 otherwise unchanged.

6. kit `platforms/kits/godot/README.md:11`: replace the Use cell with `headless CI (import, gdUnit4 by default or GUT, fails when no runner or zero tests, JUnit artifact, manual export)`. If P1-06 merged first (the cell contains `boot proof`), use `headless CI (import, boot proof, gdUnit4 by default or GUT, fails when no runner or zero tests, JUnit artifact, manual export)` so that `grep -c 'boot proof' platforms/kits/godot/README.md` still prints `1`.

7. kit `platforms/kits/github/README.md:19`: replace the sentence that reads `GUT tests only run if `addons/gut` exists.` with `Tests run with gdUnit4 (`addons/gdUnit4`, default) or GUT (`addons/gut`); the job fails when neither exists or when zero tests execute, and uploads `reports/` as the `godot-test-reports` artifact.`; every other sentence on the line stays as it is (P1-06 may have added one after the first sentence).

8. kit `CHANGELOG.md`, under `## [Unreleased]` / `### Changed`: one bullet. What: `ci-godot.yml` runs gdUnit4 by default and GUT as the alternative, fails on a missing runner or zero executed tests, uploads the reports; `testing` gains the GDScript policy (no percentage gate, pure `RefCounted` rules tested without `SceneTree`); `godot-standards`, the Godot template and both kit READMEs name gdUnit4 first. Why: assessment §4.4 and §6 D2, `reviewer.md:21`, stratics-docs DTEC-010. Proof: the grep counts and the broken-case run from Acceptance criteria.

No file is created or deleted. No manifest, `INDEX.md`, rule file or `references/*.md` changes.

## Out of scope

- The boot proof (`--quit` to `--import` plus the `SCRIPT ERROR` grep) in `godot-standards` `SKILL.md:45`, `validate-implementation/SKILL.md:41`, `reviewer.md:22`, the template lines 30 and 81, and `ci-godot.yml:34`: P1-06. This task changes `ci-godot.yml:17-18` (step name and `--import`) only because the runner needs the import (step 1).
- Movement-model wording in `godot-standards` section 3 and template lines 40, 46, 83: P1-04.
- `plugins/dev-godot/rules/godot.md` content: P2-02. Machine-specific facts and the Docker tag policy in `platforms/kits/github/README.md:19` first sentence: P2-01.
- gdtoolkit lint/format jobs in `ci-godot.yml` and in stratics-client: P3-02. The `testable-game-logic.md` reference: P3-01 (it will cite this task's command, not restate it).
- Any edit to stratics-docs `reusable-ci-godot.yml` (adding the artifact upload there) or to stratics-client: P2-15 and P3-02. Do not edit the Stratics repositories.
- The `godot-gdunit-labs/gdUnit4-action` alternative named in assessment §6 D2: not adopted here (the kit template stays runner-agnostic and image-based); mention it in the PR body only.

## Acceptance criteria

- [ ] `grep -c 'skipping tests' platforms/kits/github/workflows/ci-godot.yml` prints `0`; `grep -c 'addons/gdUnit4' platforms/kits/github/workflows/ci-godot.yml` prints `3`; `grep -c 'Overall Summary' platforms/kits/github/workflows/ci-godot.yml` prints `1`; `grep -c 'neither addons/gdUnit4 nor addons/gut' platforms/kits/github/workflows/ci-godot.yml` prints `1`.
- [ ] `grep -c 'godot --headless --path . --import' platforms/kits/github/workflows/ci-godot.yml` prints `1` (or `2` after P1-06 merges); `grep -c 'upload-artifact@v7' platforms/kits/github/workflows/ci-godot.yml` prints `2`.
- [ ] `python3 -c "import yaml; d=yaml.safe_load(open('platforms/kits/github/workflows/ci-godot.yml')); print(len(d['jobs']['import-and-test']['steps']))"` prints `4` (or `5` after P1-06 merges, which adds its `Boot proof` step; pyyaml may be absent locally; then report it as unverified and rely on CI).
- [ ] Broken-case proof (needs Godot 4.7.2 in PATH and a stratics-client checkout beside the kit; otherwise unverified): copy the `run:` block of the test step into a file, run `bash <file>` from the client root after `git lfs pull && godot --headless --path . --import` (the sprite suites load `assets/sprites/sample-0.4/*.png`, which are Git LFS pointers until pulled; stratics-docs `reusable-ci-godot.yml:88` pulls for the same reason): exit 0 and a line matching `Overall Summary: [1-9][0-9]* test cases` in `reports/gdunit.log`. Then move `addons/gdUnit4` away and rerun: exit 1 and the `::error::neither addons/gdUnit4 nor addons/gut exists` line. Restore the folder; `git -C ../stratics-client status --porcelain` prints only the untracked `reports/` you then delete. Run the proof with GNU sed/bash (Linux); on macOS use `gsed` or report the proof as unverified.
- [ ] `grep -c '^reports/$' platforms/kits/godot/.gitignore` prints `1`.
- [ ] `grep -c 'GdUnitCmdTool.gd' plugins/dev-godot/templates/project-agents-godot-2d.md` prints `1`; `grep -n 'gut_cmdln' plugins/dev-godot/templates/project-agents-godot-2d.md` prints one line, after the gdUnit4 line; `grep -c '\[gdUnit4 | GUT\]' plugins/dev-godot/templates/project-agents-godot-2d.md` prints `1`; `grep -c 'never skip tests' plugins/dev-godot/templates/project-agents-godot-2d.md` prints `1`.
- [ ] `grep -c 'GdUnitCmdTool.gd' plugins/dev-godot/skills/godot-standards/SKILL.md` prints `1`; `wc -l < plugins/dev-godot/skills/godot-standards/SKILL.md` prints a number <= 80; `diff <(sed -n 3p plugins/dev-godot/skills/godot-standards/SKILL.md) <(git show main:plugins/dev-godot/skills/godot-standards/SKILL.md | sed -n 3p)` prints nothing.
- [ ] `grep -c 'GDScript (Godot): no line, branch or mutation percentage gate' plugins/dev-core/skills/testing/SKILL.md` prints `1`; `grep -c 'scene-free test' plugins/dev-core/skills/testing/SKILL.md` prints `1`; `wc -l < plugins/dev-core/skills/testing/SKILL.md` prints a number <= 80; `diff <(sed -n 3p plugins/dev-core/skills/testing/SKILL.md) <(git show main:plugins/dev-core/skills/testing/SKILL.md | sed -n 3p)` prints nothing.
- [ ] `grep -rn 'GUT tests only run\|import + GUT + manual export' platforms/` prints nothing; `grep -c 'gdUnit4' platforms/kits/godot/README.md platforms/kits/github/README.md` prints `1` for each file.
- [ ] `git diff main --stat -- plugins/dev-godot/INDEX.md plugins/dev-core/INDEX.md plugins/dev-godot/rules/ VERSION` prints nothing.
- [ ] Gates: `platforms/tools/check.sh` reports `check: OK` for the kit files (the description budget stays at 6,805 chars); on a branch that carries `docs/plans/`, the script fails today with FAIL lines that all name a path under `docs/plans/` (17 on 2026-10-06: broken links or a missing prompts/ index); the pass condition is that no FAIL line names a file this task edits: those belong to the plan and are reported in the PR body, not fixed here; `platforms/tools/smoke.sh` prints a line starting `smoke: OK`; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` ends with `OK`; `python3 platforms/ci/validations/check_kit.py --links` exit 0.
- [ ] `sed -n '/^## \[Unreleased\]/,/^## \[10/p' CHANGELOG.md | grep -c gdUnit4` prints at least `1` (today `grep -c gdUnit4 CHANGELOG.md` prints `0`, so this gate can fail).

## Conventions

- Everything committed is in English; plain ASCII punctuation in new lines (the template's existing `→` arrows stay).
- No layout or path change: the 10.x layout is frozen; `plugins/`, `platforms/`, `docs/`, manifests and install destinations keep their paths. Nothing is renamed, created or deleted.
- `VERSION` untouched (no release in this task); `CHANGELOG.md` gets a `## [Unreleased]` entry written with evidence (what, why, proof).
- `INDEX.md` or `README.md` of every touched folder lists every entry by name: `plugins/dev-godot/INDEX.md`, `plugins/dev-core/INDEX.md`, `platforms/kits/godot/README.md` and `platforms/kits/github/README.md` already list the touched files; the two READMEs change only their descriptive cells.
- Skill descriptions stay 40-160 chars in the form "<what>. Use when <trigger>. Not for <neighbor> (skill <x>)." and are copied verbatim in the plugin `INDEX.md`; neither description changes. All skill descriptions together <= 7,200 chars (6,805 today over `plugins/*/skills/*/SKILL.md`).
- `SKILL.md` <= 80 lines (`check_kit.py` `SKILL_MAX_LINES = 80`, whole file counted).
- Templates named `^(spec|doc|project|kit)-[a-z0-9-]+\.md$`; `project-agents-godot-2d.md` keeps its name.
- `check_kit.py` resolves backtick paths ending in `.md/.sh/.json/.yml/.yaml` that start with `platforms/`, `plugins/`, `templates/`, `references/` or `../` in `platforms/**/*.md` and plugin `templates/`/`skills/` files: `../github/workflows/ci-godot.yml` in the Godot README resolves today and must keep resolving; `.gd` paths are not checked.
- `platforms/**/*.sh` rules (executable, shellcheck, bash 3.2) do not apply: no shell file changes. The kit CI's shellcheck step (`.github/workflows/ci.yml:20`) covers `platforms/tools/*.sh`, `platforms/kits/*/*.sh` and `platforms/kits/*/scripts/*.sh` only; the YAML `run:` block is validated by the broken-case proof above.
- Conventional Commits with Refs, for example `fix(kits): ci-godot runs gdUnit4 or GUT and fails instead of skipping` with `Refs: docs/plans/2026-10-kit-assessment/prompts/p1-05-godot-tests-gdunit4-never-skip.md`.
- PR body = What / Why / How I tested (literal output of the gates, the greps and the broken-case run) / Refs; tick the kit `.github/PULL_REQUEST_TEMPLATE.md` checklist.
- The executor may be Devin or Claude Code; nothing here needs Claude-specific tools.

## Report back

Final message in three blocks: done (the eight edited files, every command from Acceptance criteria with its literal result, `wc -l` of both `SKILL.md` files) · unverified (anything not run: the pyyaml step count, the broken-case run when Godot 4.7.2 or a stratics-client checkout is missing, `claude plugin validate` when `claude` is not in PATH, the GUT `-gjunit_xml_file=` flag when the GUT sources or docs could not be reached) · next step (P1-06 rebases its `ci-godot.yml` and `SKILL.md:45` edits on this branch and, when rebasing, updates its own acceptance counts: `grep -c 'shell: bash'` on `ci-godot.yml` = 2, `import-and-test` steps = 5, and it drops its "GUT step byte-identical to main" check because that step no longer exists; if P1-06 merged first, this task's `platforms/kits/godot/README.md:11` cell keeps `boot proof` after `import, ` so P1-06's `grep -c 'boot proof'` = 1 still holds; P2-15 applies the template to stratics-client; P3-01 cites this command from `testable-game-logic.md`; P3-02 adds gdtoolkit to the same workflow). Also include the proposed one-line CHANGELOG entry, for example: `ci-godot.yml` runs gdUnit4 by default or GUT as the alternative, fails when no runner exists or zero tests execute, and uploads `reports/` as a JUnit artifact; `testing` adds the GDScript policy (no percentage gate; every game rule in a pure `RefCounted` class with scene-free tests; scene tests are integration only); `godot-standards`, `project-agents-godot-2d.md` and both kit READMEs name gdUnit4 first (assessment §4.4, §6 D2; `reviewer.md:21`; stratics-docs DTEC-010).
