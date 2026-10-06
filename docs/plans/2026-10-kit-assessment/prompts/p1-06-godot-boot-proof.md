# P1-06 — Correct the Godot boot proof (--import plus SCRIPT ERROR grep)

Phase: 1 · Repos: kit · Branch to create: fix/p1-06-godot-boot-proof from main · Depends on: the assessment branch merged to main (so `docs/plans/2026-10-kit-assessment/` exists); otherwise keep the Refs path as given, it resolves after that merge. No code dependency (merge before P1-05 or rebase; both touch `ci-godot.yml`) · Effort: ~2 h

## Goal

Replace every kit occurrence of the single command `godot --path . --headless --quit` (or `godot --headless --path . --quit`) used as the Godot boot/import proof with two commands, in this order: `godot --headless --path . --import`, which imports every resource, builds the script-class cache and quits, and `! godot --headless --path . --quit 2>&1 | grep -Eq 'SCRIPT ERROR|Parser Error'`, which turns a script error printed at boot into a failing exit code. Measurable result: `grep -rn -- '--headless --quit' plugins platforms` prints nothing; every remaining `--headless --path . --quit` in `plugins/` and `platforms/` is either the `| grep -Eq 'SCRIPT ERROR|Parser Error'` form or the `tee boot.log` line of `ci-godot.yml`; the `ci-godot.yml` import step fails on a project whose autoload script has a syntax error (today it passes with exit 0).

## Why

- assessment §4.4 (Exit code do Godot): `godot-standards` and `validate-implementation` use `godot --headless --quit` as the proof, but the exit code is 0 even after a `SCRIPT ERROR`; the project found this and switched to `grep -q 'SCRIPT ERROR'` (ARCHITECT.md delta 6). The kit has not absorbed it.
- assessment §6 item D3: replace `--headless --quit` with `--headless --import` (official docs: imports all resources and quits; `--headless` is required without a GPU) followed by `! godot --headless --path . --quit 2>&1 | grep -q 'SCRIPT ERROR'` in `godot-standards`, `validate-implementation`, `reviewer` and the CI template. assessment §8 puts D3 in week 1.
- stratics-docs `docs/spec/ARCHITECT.md:74-76`: "6. [DECISION] 2026-10-05 **Client boot proofs** never rely on the exit code of `godot --quit`, which is 0 even after script errors. Use `! godot --headless --path . --quit 2>&1 | grep -q 'SCRIPT ERROR'` together with the gdUnit4 run (client CI)."
- stratics-docs `.github/workflows/reusable-ci-godot.yml:89-92`, comment on the import step: "`--quit` skips the import scan, so class_name scripts such as gdUnit4's GdUnitTestCIRunner stay unregistered on a fresh checkout and the runner fails to load (stratics-docs#84 / client CI 37213891040)"; the step runs `godot --headless --path . --import`. stratics-client `.github/workflows/ci.yml:50` runs the same. The kit template still ships `--quit`, so a new project copies a step the project already had to fix.
- Official Godot CLI reference (`tutorials/editor/command_line_tutorial.rst` in godotengine/godot-docs; verify against the page for the project's engine version before relying on it): `--import` "Starts the editor, waits for any resources to be imported, and then quits. Implies `--editor` and `--quit`"; `--headless` "Enable headless mode (`--display-driver headless --audio-driver Dummy`)" and "is **required** on platforms that do not have GPU access (such as continuous integration)".
- The same kit forbids this class of gate: `plugins/quality-core/agents/reviewer.md:21` "A proof that cannot fail ... proves nothing, so check that it would fail on a broken case." The current boot proof cannot fail on a script error.

## Current state

- kit `platforms/kits/github/workflows/ci-godot.yml` (42 lines; container `barichello/godot-ci:4.7.2`; no `shell:` key anywhere, so container steps run under `sh -e`):
  `ci-godot.yml:17` `      - name: Project import (generates .godot/, validates resources)`
  `ci-godot.yml:18` `        run: godot --headless --path . --quit`
  `ci-godot.yml:19-25` the GUT test step (owned by P1-05; do not touch).
  `ci-godot.yml:33` `      - name: Import`
  `ci-godot.yml:34` `        run: godot --headless --path . --quit`
- kit `plugins/dev-godot/skills/godot-standards/SKILL.md` (47 lines; description on line 3 must not change):
  `SKILL.md:43` `## 5. Verify`
  `SKILL.md:45` `Run `godot --path . --headless --quit` and the project test command. Treat parser/import errors as failures and report the literal output.`
  `SKILL.md:47` `Done when: ... and headless import plus tests pass.` (P1-04 appends to this line; leave it alone here.)
- kit `plugins/quality-core/agents/reviewer.md` (31 lines; the `## Report (at most 80 lines)` block on lines 25-31 must stay byte-identical):
  `reviewer.md:22` `3. Gates: run the commands named there. Kit fallbacks: `./mvnw -q spotless:check verify` (Java), `godot --path . --headless --quit` plus the project test runner (Godot), `platforms/tools/check.sh` (kit/spec). Keep the literal failing excerpt.`
- kit `plugins/quality-core/skills/validate-implementation/SKILL.md` (68 lines):
  `SKILL.md:41` `| Godot | `godot --path . --headless --quit` plus the project test runner |`
- kit `plugins/dev-godot/templates/project-agents-godot-2d.md` (87 lines):
  `project-agents-godot-2d.md:30` `godot --path . --headless --quit                # import assets/validate project (CI)`
  `project-agents-godot-2d.md:31` `godot --path . --headless -s addons/gut/gut_cmdln.gd   # run GUT (adjust to the framework)` (P1-05; do not touch)
  `project-agents-godot-2d.md:81` `- Always: run `--headless --quit` after touching assets; test a scene in isolation (F6) before the whole stage.`
- kit `platforms/kits/godot/README.md:11` `| `../github/workflows/ci-godot.yml` | headless CI (import + GUT + manual export) |`
- kit `platforms/kits/github/README.md:19` `- `ci-godot.yml` uses `barichello/godot-ci:4.7.2` (tag verified on Docker Hub on 2026-09-29). GUT tests only run if `addons/gut` exists. Windows/macOS export only via `workflow_dispatch` and requires `export_presets.cfg` committed to the repo.`
- kit `CHANGELOG.md`: `### Changed` already exists under `## [Unreleased]`; append the bullet there.
- kit `plugins/dev-godot/INDEX.md:8` and `plugins/quality-core/INDEX.md:8` repeat the two skill descriptions verbatim; neither description changes, so neither index changes.

## Change

Use the flag order `--headless --path .` everywhere (the assessment, ARCHITECT.md delta 6 and both Stratics workflows use it), so one grep finds every occurrence.

Line numbers below are those of `main` before this task; edit each file bottom-up or match the quoted content, because the earlier edit in a file shifts the later lines (+5 in `ci-godot.yml`, +1 in the template).

1. kit `platforms/kits/github/workflows/ci-godot.yml`: replace lines 17-18 with this block, verbatim (same 6-space indentation as the neighbouring steps):

```yaml
      - name: Project import (generates .godot/ and the script-class cache, validates resources)
        run: godot --headless --path . --import
      - name: Boot proof (the exit code of --quit is 0 after a script error, so the log is the gate)
        shell: bash
        run: |
          godot --headless --path . --quit 2>&1 | tee boot.log
          ! grep -Eq 'SCRIPT ERROR|Parser Error' boot.log
```

   Why two commands instead of the one-line `! godot ... | grep` form: `shell: bash` on GitHub Actions runs `bash -eo pipefail`, and under `pipefail` a Godot crash (non-zero exit) would make the negated pipeline succeed even when the log contains `SCRIPT ERROR`. Line one keeps the crash as a failure (the status quo of the old step; a non-zero exit here is a real boot failure; the Godot 4.7.2 shutdown segfault noted in stratics-client `ci.yml:52-54` affects editor-mode exports, not `--quit` without `--editor`); line two adds the log check. The `! grep` line must stay the last line of the step: under `bash -e` a negated command never aborts the script, only its status as the final command fails the step (a line appended after it later, for example by P3-02 or a project, would silently mask the failure). Replace the export job's `run: godot --headless --path . --quit` line (main line 34; line 39 after the step-1 block) with `        run: godot --headless --path . --import` and keep its `- name: Import` line; the export job needs no grep because `import-and-test` also runs on `workflow_dispatch`; the job keeps its own explicit `--import` step (the docs state `Implies --import` only for `--export-debug` and `--export-pack`). Lines 19-25 stay byte-identical (P1-05 rewrites them).

2. kit `plugins/dev-godot/skills/godot-standards/SKILL.md`: replace line 45 with these two lines, verbatim:

```markdown
Boot proof, two commands in this order: `godot --headless --path . --import` (imports every resource, builds the script-class cache, quits; `--headless` is mandatory without a GPU), then `! godot --headless --path . --quit 2>&1 | grep -Eq 'SCRIPT ERROR|Parser Error'` (the exit code of `--quit` is 0 after a script error, so a match is the failure). Then run the project test command.
Report the literal output of all three; a `SCRIPT ERROR`, `Parser Error` or import error is a failure even when the exit code is 0.
```

   On Godot 4 the matching token is `SCRIPT ERROR` (the engine prints `SCRIPT ERROR: Parse Error: ...`); `Parser Error` is kept as a defensive alternative and matches nothing on 4.x. Resulting length: 48 lines (limit 80). Frontmatter, sections 1-4 and the `Done when` line stay unchanged.

3. kit `plugins/quality-core/agents/reviewer.md`: on line 22 replace the fragment `` `godot --path . --headless --quit` plus the project test runner (Godot) `` with `` `godot --headless --path . --import` then `! godot --headless --path . --quit 2>&1 | grep -Eq 'SCRIPT ERROR|Parser Error'` plus the project test runner (Godot) ``. Nothing else on the line or in the file changes; lines 25-31 stay byte-identical.

4. kit `plugins/quality-core/skills/validate-implementation/SKILL.md`: replace line 41 with one table row, verbatim:

```markdown
| Godot | `godot --headless --path . --import`, then the boot-proof grep of the `--quit` log from skill `godot-standards` section 5 (`--quit` exits 0 after a `SCRIPT ERROR`), plus the project test runner |
```

   No unescaped `|` inside the row: GFM splits a cell on a pipe even inside a code span (escaping it as `\|` would make the raw command wrong when copied); `check_kit.py` does not parse tables. Row count of the table stays 3.

5. kit `plugins/dev-godot/templates/project-agents-godot-2d.md`:
   a. Replace line 30 with these two lines (keep the column alignment of the comments roughly as the block does today):

```bash
godot --headless --path . --import                                # import assets, build the script-class cache (CI)
! godot --headless --path . --quit 2>&1 | grep -Eq 'SCRIPT ERROR|Parser Error'   # boot proof: --quit exits 0 after a script error
```

   b. Replace main line 81 (line 82 after 5a) with: `- Always: run the two boot-proof commands from Commands after touching assets or scripts; test a scene in isolation (F6) before the whole stage.`
   c. Lines 29, 31-32 and every other line stay unchanged.

6. kit `platforms/kits/godot/README.md:11`: if the Use cell still reads `headless CI (import + GUT + manual export)`, replace it with `headless CI (import + boot proof + GUT + manual export)`. If P1-05 merged first and the cell starts with `headless CI (import, `, insert `boot proof, ` immediately after `import, ` and change nothing else; either way `grep -c 'boot proof' platforms/kits/godot/README.md` must print `1`.

7. kit `platforms/kits/github/README.md`: on line 19 insert, after the first sentence (`... on 2026-09-29).`), this sentence: `The import step runs `--import` (not `--quit`, which skips the import scan) and a boot-proof step greps the `--quit` log for `SCRIPT ERROR|Parser Error`, because that exit code is 0 after a script error.` The GUT and export sentences stay as they are.

8. kit `CHANGELOG.md`, under `## [Unreleased]` / `### Changed`: one bullet. What: the Godot boot proof in `godot-standards` §5, `reviewer` step 3, `validate-implementation` §3, the `project-agents-godot-2d.md` template and `ci-godot.yml` is now `--import` plus a `SCRIPT ERROR|Parser Error` grep of the `--quit` log. Why: `--quit` exits 0 after a script error and skips the import scan (assessment §4.4, §6 D3; stratics-docs ARCHITECT.md delta 6, 2026-10-05; stratics-docs#84). Proof: the greps from Acceptance criteria and the broken-case run (literal output).

No file is created or deleted. No manifest, rule, reference, `INDEX.md` or `VERSION` changes.

## Out of scope

- `ci-godot.yml:19-25` (test job: gdUnit4 default, no silent skip, zero-test failure), `project-agents-godot-2d.md:8` and `:31`, and the GUT sentence in `platforms/kits/github/README.md:19`: P1-05. If P1-05 merges first, rebase and keep its test step untouched.
- P1-05 rewrites the rest of the `platforms/kits/godot/README.md:11` Use cell; when it rebases on this PR it must keep `boot proof` in the cell.
- Movement lines in `godot-standards` §3 and the template (`project-agents-godot-2d.md:40`, `:83`): P1-04.
- `plugins/dev-godot/rules/godot.md` content: P2-02 writes the rule's boot-proof line; it must use the same two commands and the same regex `grep -Eq 'SCRIPT ERROR|Parser Error'` as this task (P2-02 currently says `grep -q 'SCRIPT ERROR'`).
- stratics-client `AGENTS.md:31` and `:59` (still `--headless --quit`): P2-15 regenerates it from the template (p3-03 attributes these lines to P1-06; that is stale, the owner is P2-15). Do not edit the Stratics repositories.
- gdtoolkit lint/format steps in `ci-godot.yml` and the client CI: P3-02.
- Adding the boot-proof grep to stratics-docs `.github/workflows/reusable-ci-godot.yml` (it has `--import` at line 92 but no `SCRIPT ERROR` grep): no prompt owns it; name it in the PR body as a follow-up for the spec repository.
- Online 2D references and generated-file rules (`*.uid`, `*.import`): P3-01 and D4.

## Acceptance criteria

- [ ] `grep -rn -- '--headless --quit' plugins platforms` prints nothing (exit 1).
- [ ] `grep -rn -- '--path . --headless --quit' plugins platforms` prints nothing (exit 1).
- [ ] `grep -rn -- '--headless --path . --quit' plugins platforms | grep -v 'SCRIPT ERROR|Parser Error' | grep -v 'boot.log'` prints nothing (every remaining `--quit` is the grep form or the `tee boot.log` line).
- [ ] `grep -rl -- '--headless --path . --import' plugins platforms | sort` prints exactly these five paths: `platforms/kits/github/workflows/ci-godot.yml`, `plugins/dev-godot/skills/godot-standards/SKILL.md`, `plugins/dev-godot/templates/project-agents-godot-2d.md`, `plugins/quality-core/agents/reviewer.md`, `plugins/quality-core/skills/validate-implementation/SKILL.md`.
- [ ] `grep -c -- '--headless --path . --import' platforms/kits/github/workflows/ci-godot.yml` prints `2`; `grep -c "grep -Eq 'SCRIPT ERROR|Parser Error' boot.log" platforms/kits/github/workflows/ci-godot.yml` prints `1`; `grep -c 'shell: bash' platforms/kits/github/workflows/ci-godot.yml` prints `1` (`2` if P1-05 merged first).
- [ ] `python3 -c "import yaml,sys; d=yaml.safe_load(open('platforms/kits/github/workflows/ci-godot.yml')); print(len(d['jobs']['import-and-test']['steps']), len(d['jobs']['export']['steps']))"` prints `4 5` (`5 5` if P1-05 merged first; pyyaml is a kit CI dependency; if missing locally, `pip3 install --user pyyaml`).
- [ ] The GUT test step (main lines 19-25, now lines 24-30 after the five inserted lines) is byte-identical to main: `diff <(sed -n 24,30p platforms/kits/github/workflows/ci-godot.yml) <(git show main:platforms/kits/github/workflows/ci-godot.yml | sed -n 19,25p)` prints nothing. If P1-05 merged first, drop this check: the test step is P1-05's and is covered by its own acceptance criteria (P1-05's Report back says the same). Do not compare from the test step to end of file (`,$p`): that range includes the export job's `- name: Import` step, whose line this task changes from `--quit` to `--import`, so such a diff always prints that line.
- [ ] `wc -l < plugins/dev-godot/skills/godot-standards/SKILL.md` prints a number <= 80 (expected 48; 52 if P1-04 merged first; 50 if P1-05 merged first; 54 if both merged first); `diff <(sed -n 3p plugins/dev-godot/skills/godot-standards/SKILL.md) <(git show main:plugins/dev-godot/skills/godot-standards/SKILL.md | sed -n 3p)` prints nothing.
- [ ] `diff <(sed -n 25,31p plugins/quality-core/agents/reviewer.md) <(git show main:plugins/quality-core/agents/reviewer.md | sed -n 25,31p)` prints nothing (report format intact); `wc -l < plugins/quality-core/agents/reviewer.md` prints `31`.
- [ ] `grep -c '^| Godot |' plugins/quality-core/skills/validate-implementation/SKILL.md` prints `1` and that line contains both `--import` and `SCRIPT ERROR`.
- [ ] `grep -c 'boot-proof commands' plugins/dev-godot/templates/project-agents-godot-2d.md` prints `1`; `grep -c '^godot --headless --path . --import' plugins/dev-godot/templates/project-agents-godot-2d.md` prints `1`; `grep -c 'HealthComponent' plugins/dev-godot/templates/project-agents-godot-2d.md` prints `2` (unchanged).
- [ ] `grep -c 'boot proof' platforms/kits/godot/README.md` prints `1`; `grep -c 'boot-proof step' platforms/kits/github/README.md` prints `1`.
- [ ] `git diff main --stat -- plugins/dev-godot/INDEX.md plugins/quality-core/INDEX.md plugins/dev-godot/rules/ VERSION` prints nothing.
- [ ] Broken case, run where a Godot 4.x binary is on PATH (the stratics-client checkout or any Godot 4 project with an autoload): append the line `this is not gdscript` to a script loaded at boot (in stratics-client: `autoload/event_bus.gd`, listed under `[autoload]` in `project.godot`), run `godot --headless --path . --import; godot --headless --path . --quit 2>&1 | tee /tmp/boot.log; ! grep -Eq 'SCRIPT ERROR|Parser Error' /tmp/boot.log; echo "exit=$?"`, expect `exit=1` plus a line starting `SCRIPT ERROR: Parse Error:` in the tee output; revert with `git checkout -- autoload/event_bus.gd` and re-run, expect `exit=0` and no such line. Paste both outputs in the PR body. Without a Godot binary, report this item as unverified; do not claim it.
- [ ] Gates: `platforms/tools/check.sh` exit 0; `platforms/tools/smoke.sh` prints `smoke: OK`; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` ends with `OK`; `python3 platforms/ci/validations/check_kit.py --links` exit 0. If `check_kit.py` fails only on files under `docs/plans/`, paste the FAIL lines in the PR body as a pre-existing blocker and do not edit those files.
- [ ] `grep -c 'Parser Error' CHANGELOG.md` prints at least `1`, inside `## [Unreleased]`.

## Conventions

- Everything committed is in English; plain ASCII punctuation in new lines (the template's existing `→` lines are not touched).
- No layout or path change: the 10.x layout is frozen; `plugins/`, `platforms/`, `docs/`, manifests and install destinations keep their paths. Nothing is renamed, created or deleted.
- `VERSION` untouched (no release in this task).
- `CHANGELOG.md` gets a `## [Unreleased]` entry written with evidence (what, why, proof).
- `INDEX.md` or `README.md` of every touched folder lists every entry by name: `plugins/dev-godot/INDEX.md`, `plugins/quality-core/INDEX.md`, `platforms/kits/godot/README.md` and `platforms/kits/github/README.md` already list the touched files; the two README edits above change a description cell and a note, not the entry list.
- Skill descriptions stay unchanged (40-160 chars, "<what>. Use when <trigger>. Not for <neighbor> (skill <x>)."), copied verbatim in each plugin `INDEX.md`; the budget stays at 6,805 of 7,200 chars.
- `SKILL.md` <= 80 lines (`check_kit.py` `SKILL_MAX_LINES = 80`, whole file counted). `reviewer.md` keeps its `## Report (at most 80 lines)` format and its `allowed-tools`/`tools` lists.
- Templates keep the name pattern `^(spec|doc|project|kit)-[a-z0-9-]+\.md$`; `project-agents-godot-2d.md` keeps its name.
- `check_kit.py` validates backtick paths with a `.md|.sh|.json|.yml|.yaml` extension in `plugins/*/templates/*.md` and `platforms/**/*.md`: the new text adds none (`boot.log` is not in backticks with one of those extensions; `../github/workflows/ci-godot.yml` already resolves).
- The YAML must stay a valid GitHub Actions workflow: `shell: bash` is a step key next to `run:`; keep the two-space list indentation of the file.
- Conventional Commits with Refs, for example `fix(kits,dev-godot,quality-core): Godot boot proof is --import plus a SCRIPT ERROR grep` and `Refs: docs/plans/2026-10-kit-assessment/prompts/p1-06-godot-boot-proof.md`.
- PR body = What / Why / How I tested (literal output of the gates, the greps and the broken case) / Refs; tick the kit's `.github/PULL_REQUEST_TEMPLATE.md` checklist.
- The executor may be Devin or Claude Code; nothing here needs Claude-specific tools.

## Report back

Final message in three blocks: done (the seven edited files plus `CHANGELOG.md`, every command from Acceptance criteria with its literal result, `wc -l` of both `SKILL.md` files and of `reviewer.md`) · unverified (anything not run: the broken case when no Godot binary is available, the pyyaml step count when pyyaml is missing, `claude plugin validate` when `claude` is not in PATH) · next step (P1-05 rewrites the test step of the same `ci-godot.yml` and the GUT lines; P2-15 regenerates stratics-client `AGENTS.md` from the template; the stratics-docs `reusable-ci-godot.yml` grep is a follow-up for the spec repository). Also include the proposed one-line CHANGELOG entry, for example: Godot boot proof in `godot-standards` §5, `reviewer` step 3, `validate-implementation` §3, the `project-agents-godot-2d.md` template and `ci-godot.yml` is now `godot --headless --path . --import` followed by `! godot --headless --path . --quit 2>&1 | grep -Eq 'SCRIPT ERROR|Parser Error'`, because `--quit` exits 0 after a script error and skips the import scan (assessment §4.4, §6 D3; stratics-docs ARCHITECT.md delta 6; stratics-docs#84).
