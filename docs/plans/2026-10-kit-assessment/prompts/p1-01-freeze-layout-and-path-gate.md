# P1-01 — Freeze the 10.x layout and add a stale-path gate

Phase: 1 · Repos: kit · Branch to create: feat/p1-01-freeze-layout-and-path-gate from main · Depends on: none · Effort: ~4 h

## Goal

Declare the agent-rules-kit 10.x layout frozen (no path or install-destination change before 2027-01-01, content changes are MINOR/PATCH), remove the kit's own stale layout references, and make `platforms/tools/sync-project.sh --check <repo>` fail when a consumer repository cites an obsolete kit path. Measurable result: after this task, `sync-project.sh --check` run against stratics-docs reports the 6 stale lines in 4 files that exist there today (0 in stratics-client and stratics-server), and a unit test in the kit's CI proves the gate fails on a throwaway repo with one stale citation and passes with the opt-out marker.

## Why

- assessment §4.1: `CHANGELOG.md` records v1.0.0 on 2026-09-29 and v10.1.0 on 2026-10-04, with layout changes in 4.0, 6.0, 8.0, 9.0 and 10.0 (kit `CHANGELOG.md:195`, `:141`, `:58`, `:52`, `:33`). Every layout change forces `bootstrap`/`doctor` re-runs on every machine and invalidates citations in the consumer specs.
- assessment §6 item A3 asks to freeze the layout for at least a quarter, treat paths as a contract, and add a cited-paths gate reachable through `sync-project.sh --check <repo>`; assessment §8 puts A3 in week 1, before any content work.
- Consumer drift measured today: stratics-docs `AGENTS.md:20` cites `agents/skills/process/README.md` (layout v4 to v7); `docs/spec/decisions/DTEC-001-java-25-lts.md:19` and `:43` cite `kits/java-maven/pom-parent.xml` and `rules/java/build-and-dependencies.md`; `docs/spec/decisions/DTEC-002-stack-cliente-servidor-banco.md:50` cites `rules/godot/godot-2d.md`; `docs/spec/decisions/DTEC-003-redis-condicionado.md:20` and `:44` cite `knowledge/redis/`. None of these paths exist in the kit (verified with `ls agents rules knowledge kits processes platforms/install plugins/ai-kit` at the kit root: all absent). Fixing them is P1-02; this task adds the gate that keeps them fixed.
- The kit itself is stale: `docs/projects.md:3` cites `platforms/install/` (removed in 8.0, `CHANGELOG.md:64`) and `docs/projects.md:3` and `:23` still describe "knowledge" as installed content (removed in 6.0 and 8.0). `.github/PULL_REQUEST_TEMPLATE.md:6` asks to bump `LAYOUT_VERSION`, a file that no longer exists (`ls LAYOUT_VERSION` fails).
- `docs/maintenance.md:7` already says a layout change is MAJOR but names no freeze window and does not classify content changes; `docs/design.md` has no stability principle at all.

## Current state

- kit `docs/design.md:20` (last bullet of `## Principles`; the new principle goes right after it):
  `- **Everything validatable.** Layout, manifests, frontmatter, budgets, indexes, links and vendor locks are mechanical CI gates.`
- kit `docs/maintenance.md:7`:
  `A layout or installation-destination change is a SemVer MAJOR change. There is no separate layout version: migration behavior belongs in `bootstrap.sh`, `doctor.sh` and the release notes.`
- kit `docs/projects.md:3`:
  `Rules, skills and knowledge stay **in the kit** and are installed on the machine (`platforms/install/`). The project only receives its own artifacts. Real example: `~/Documents/GitHub/stratics-docs`.`
- kit `docs/projects.md:23`:
  `- Skills (including the normative rules, now under `plugins/*/skills/`) and knowledge: installed on the agent's machine — the project does not copy them.`
- kit `.github/PULL_REQUEST_TEMPLATE.md:6`:
  `- [ ] `LAYOUT_VERSION` bumped if a folder or install destination changed`
- kit `platforms/tools/sync-project.sh:3-4` (usage header) and `:24-37` (check mode). Line 34 is the last check before the verdict:
  `  [[ -f "$REPO/.github/workflows/spec-lint.yml" ]] || { echo "sync: spec-lint.yml missing"; FAILED=1; }`
  `  if [[ $FAILED -eq 0 ]]; then echo "sync: $REPO consistent with kit $expected"; else exit 1; fi`
- kit `platforms/tools/INDEX.md:11`:
  `| `sync-project.sh` | copies spec validation files into a project; `--check` compares | initialize or refresh project spec CI |`
- kit `platforms/ci/validations/INDEX.md:8` (last table row; the new test row goes after it):
  `| `test_check_spec.py` | `check_spec.py` FEAT↔REQ cross-check (unittest) | the kit's CI |`
- kit `platforms/ci/validations/test_sync_project.py` (new file); must be listed in `platforms/ci/validations/INDEX.md`. CI already discovers it: `.github/workflows/ci.yml:28` runs `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`.
- kit `CHANGELOG.md:5-16`: `## [Unreleased]` exists with `### Added` and `### Changed` sections; append to them.

## Change

1. kit `docs/design.md`: insert one bullet after line 20, inside `## Principles`:

```markdown
- **Layout stability.** The 10.x layout is frozen until at least 2027-01-01: `plugins/`, `platforms/`, `docs/`, the plugin and marketplace manifests (`.devin-plugin/`, `.claude-plugin/`, `plugin.json`, `.agents/plugins/`) and the install destinations (`~/.ai-kit`, `~/.codex/AGENTS.md`, `~/.claude/CLAUDE.md`, the marketplace plugin caches) keep their paths. A path or destination change is a SemVer MAJOR release and ships with a deprecation note in `CHANGELOG.md` and a `doctor.sh` migration; content changes are MINOR or PATCH. Consumer repositories cite kit paths, so `sync-project.sh --check` fails on citations of removed layouts.
```

2. kit `docs/maintenance.md`: replace line 7 with:

```markdown
The 10.x layout is frozen until at least 2027-01-01 (principle "Layout stability" in [design.md](design.md)). A layout or installation-destination change is a SemVer MAJOR change and ships with a deprecation note in the release notes plus a migration in `bootstrap.sh` and `doctor.sh`. A content change is MINOR when it adds a rule, skill, reference, template, validator gate or document, and PATCH when it corrects one without changing routing. There is no separate layout version.
```

3. kit `docs/projects.md`: rewrite line 3 so it says that rules, skills, references and templates stay in the kit under `plugins/` and reach the agent through the plugin marketplaces or `bootstrap.sh` (no `platforms/install/`, no "knowledge"); keep the "Real example" clause unchanged (P2-01 owns machine paths). Rewrite line 23 to "Skills, rules and references (under `plugins/*/`): consumed through the agent's plugin install, the project does not copy them." Run `grep -n 'platforms/install\|knowledge' docs/projects.md` and expect 0 lines.

4. kit `.github/PULL_REQUEST_TEMPLATE.md`: replace line 6 with `- [ ] No folder or install destination changed (10.x layout frozen; see docs/design.md "Layout stability"); if one did, this PR is MAJOR with a deprecation note and a doctor.sh migration`.

5. kit `platforms/tools/sync-project.sh`: add the stale-kit-paths scan to check mode. Define the list and the function above the `if [[ "$MODE" == check ]]` block, then call `scan_stale_kit_paths "$REPO" || FAILED=1` on a new line after line 34. Use this verbatim (bash 3.2: no associative arrays, no `mapfile`):

```bash
# Obsolete kit paths (layouts 1.x to 9.x). A consumer line that must keep one
# (historical citation) appends the marker "<!-- kit-path-ok -->".
STALE_KIT_PATHS='agents/skills/|agents/rules/|agents/knowledge/|rules/godot/|rules/java/|kits/java-maven/|kits/github/|platforms/install/|knowledge/|processes/sdd/|plugins/ai-kit/'
STALE_OPT_OUT='<!-- kit-path-ok -->'

scan_stale_kit_paths() { # $1 = repo dir; prints one line per stale citation; returns 1 if any
  local hits
  hits="$(grep -rnE --include='*.md' --exclude-dir=.git --exclude-dir=node_modules \
      "(^|[^/A-Za-z0-9_.-])($STALE_KIT_PATHS)" "$1" 2>/dev/null \
    | sed "s|^$1/||" \
    | grep -vE '(^|/)(legacy|docs/sessions)/' \
    | grep -vF -- "$STALE_OPT_OUT" || true)"
  [[ -n "$hits" ]] || return 0
  printf '%s\n' "$hits" | sed 's|^|sync: stale kit path: |'
  echo "sync: the 10.x layout is frozen (docs/design.md, Layout stability); fix the citation or append $STALE_OPT_OUT"
  return 1
}
```

   The anchor `(^|[^/A-Za-z0-9_.-])` keeps current paths such as `platforms/kits/github/workflows/spec-lint.yml` and `.claude/rules/godot/...` out of the match. Update the usage comment on lines 3-4 to say `--check` also scans `*.md` for obsolete kit paths. Update `platforms/tools/INDEX.md:11` to: `| `sync-project.sh` | copies spec validation files into a project; `--check` compares the copy and scans the repo's `*.md` for obsolete kit paths | initialize or refresh project spec CI; in the project's CI |`.

6. kit `platforms/ci/validations/test_sync_project.py` (new file, unittest, <=90 lines, pattern of `test_check_spec.py`: `subprocess.run` with `capture_output=True, text=True`). In `setUp` create a `tempfile.TemporaryDirectory`, run `platforms/tools/sync-project.sh <tmp>` once (install mode, needs `shasum`, no git). Four tests:
   - clean repo: `--check` exit 0, stdout contains `consistent with kit`;
   - `docs/spec/decisions/DTEC-001-x.md` whose line 3 is `- agent-rules-kit `kits/java-maven/pom-parent.xml` requires [25,26)`: exit 1, output contains `stale kit path: docs/spec/decisions/DTEC-001-x.md:3`;
   - same line plus ` <!-- kit-path-ok -->` appended: exit 0;
   - no false positives: a file citing `platforms/kits/github/workflows/spec-lint.yml` and a `docs/sessions/2026-01-01-x.md` citing `agents/skills/`: exit 0.
   Add the row `| `test_sync_project.py` | `sync-project.sh --check` stale-kit-path scan on a throwaway repo (unittest) | the kit's CI |` to `platforms/ci/validations/INDEX.md`. Do not touch `smoke.sh`: it is 492 lines of bootstrap/doctor lifecycle and CI already runs unittest discovery.

7. kit `CHANGELOG.md` under `## [Unreleased]`: one `### Added` bullet for the scan and its test, one `### Changed` bullet for the freeze (design, maintenance, PR template) and the `projects.md` fix. Write what, why and proof, citing the stratics-docs lines from Why and the `ls` evidence that the paths are gone.

## Out of scope

- Fixing the stale citations inside stratics-docs (`AGENTS.md:20`, DTEC-001, DTEC-002, DTEC-003): P1-02. This task only makes them visible.
- Removing `~/Documents/GitHub/stratics-docs` and other machine-specific facts from `docs/projects.md` and references: P2-01.
- Running `sync-project.sh --check` in the three Stratics CIs and generating `CLAUDE.md`, `.claude/settings.json`, rules or skills per repo: P2-04, P2-05, P2-06, P2-15.
- Any change to `check_kit.py` layout rules, plugin manifests, `VERSION` or install destinations. Nothing moves in this task.

## Acceptance criteria

- [ ] `grep -c 'Layout stability' docs/design.md` prints `1`; `grep -c '2027-01-01' docs/design.md docs/maintenance.md` prints `1` for each file.
- [ ] `grep -n 'platforms/install\|knowledge' docs/projects.md` prints nothing (exit 1).
- [ ] `grep -c 'LAYOUT_VERSION' .github/PULL_REQUEST_TEMPLATE.md` prints `0`.
- [ ] `grep -c 'kit-path-ok' platforms/tools/sync-project.sh` prints at least `2` (definition and message).
- [ ] `shellcheck platforms/tools/sync-project.sh` exits 0; `bash -n platforms/tools/sync-project.sh` exits 0; `test -x platforms/tools/sync-project.sh` exits 0. If macOS `/bin/bash` 3.2 is available, `/bin/bash -n platforms/tools/sync-project.sh` exits 0 too.
- [ ] `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` ends with `OK` and reports at least 4 more tests than on main (count with `-v`).
- [ ] With a stratics-docs checkout beside the kit: `platforms/tools/sync-project.sh --check ../stratics-docs` exits 1 and prints exactly 6 `sync: stale kit path:` lines (`AGENTS.md:20`, DTEC-001 `:19` and `:43`, DTEC-002 `:50`, DTEC-003 `:20` and `:44`); verify the count first with `grep -rnE --include='*.md' '(^|[^/A-Za-z0-9_.-])(agents/skills/|rules/godot/|rules/java/|kits/java-maven/|knowledge/)' ../stratics-docs | grep -v docs/sessions | wc -l`. Against `../stratics-client` and `../stratics-server` the scan prints no stale line (the check may still fail on a missing `spec-lint/`; that is expected and unrelated).
- [ ] Gates: `platforms/tools/check.sh` exit 0; `platforms/tools/smoke.sh` prints `smoke: OK`; `python3 platforms/ci/validations/check_kit.py --links` exit 0.
- [ ] `grep -c 'stale kit path\|Layout stability\|layout frozen' CHANGELOG.md` prints at least `2`, all inside `## [Unreleased]`.

## Conventions

- Everything committed is in English; plain ASCII punctuation in new lines.
- No layout or path change: the 10.x layout is frozen; `plugins/`, `platforms/`, `docs/`, manifests and install destinations keep their paths. This task is the one that writes that rule down.
- `VERSION` untouched (no release in this task).
- `CHANGELOG.md` gets `## [Unreleased]` entries written with evidence (what, why, proof).
- `INDEX.md` or `README.md` of every touched folder lists every entry by name (a folder never has both): `platforms/tools/INDEX.md`, `platforms/ci/validations/INDEX.md`. `docs/` already lists `design.md`, `maintenance.md`, `projects.md`.
- Every `platforms/**/*.sh` is executable, passes shellcheck and parses under bash 3.2 (`docs/maintenance.md:54`: avoid unquoted text after a quoted string inside `"$(...)"`).
- `check_kit.py` validates backtick paths with a file extension in `docs/*.md` and `platforms/**/*.md` (`platforms/ci/validations/check_kit.py:831-835`): never write an obsolete path with an extension inside backticks in those files; bare directory names such as `platforms/install/` are not matched, but prefer prose.
- Conventional Commits with Refs, for example `feat(sync-project): stale kit path scan in --check; freeze the 10.x layout` and `Refs: docs/plans/2026-10-kit-assessment/prompts/p1-01-freeze-layout-and-path-gate.md`.
- PR body = What / Why / How I tested (literal output of the gates and of the stratics-docs scan) / Refs; also tick the kit's `.github/PULL_REQUEST_TEMPLATE.md` checklist.
- The executor may be Devin or Claude Code; nothing here needs Claude-specific tools.

## Report back

Final message in three blocks: done (every path created or edited, each command from Acceptance criteria with its literal result, including the 6 stale lines printed for stratics-docs) · unverified (anything not run, for example bash 3.2 parse when no macOS shell exists, or a Stratics checkout not available) · next step (P1-02 fixes the six citations; P2-15 wires `sync-project.sh --check` into the Stratics CIs). Also include the proposed one-line CHANGELOG entry, for example: `sync-project.sh --check` now scans the project's `*.md` for obsolete kit paths (layouts 1.x to 9.x) and fails listing `file:line`, with a `<!-- kit-path-ok -->` opt-out; the 10.x layout is declared frozen until 2027-01-01 in `docs/design.md` and `docs/maintenance.md`.
