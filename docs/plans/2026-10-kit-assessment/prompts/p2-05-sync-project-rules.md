# P2-05 — sync-project.sh generates .claude/rules from kit rules

Phase: 2 · Repos: kit (agent-rules-kit) · Branch to create: feat/p2-05-sync-project-rules from main · Depends on: P2-04 (P2-02 may land before or after) · Effort: ~4 h

## Goal

Extend `platforms/tools/sync-project.sh` so that, for each plugin the repo's profile enables (the P2-04 mapping), it copies `plugins/<plugin>/rules/*.md` into `<repo>/.claude/rules/<plugin>-<rule>.md` with a generated marker line, and so that `--check` reports drift between the copies and the kit. Add an `AI_KIT_USER_RULES` switch to `doctor.sh` (default `1`) that skips the machine-level `~/.claude/rules/` symlinks, so a repo carrying `.claude/rules` does not load every rule twice. Measurable result: a clean clone with no `~/.ai-kit`, opened in Claude Code web, a GitHub Actions runner or a new machine, receives the same path-scoped rules as the owner's machine; today it receives none (assessment §4.2).

## Why

- assessment §4.2: the kit is delivered by symlinks in `~/.claude/rules/`; none of the three Stratics repos has `.claude/rules`, so cloud sessions, runners and collaborators without `bootstrap.sh` run "without any global rule, skill or hook"; the 2026 practice is "the repository carries what the agent needs", distributed by commit through an extended `sync-project.sh`.
- assessment §5 (rules row): path rules in `.claude/rules/*.md` with `paths:` are the official mechanism (confirmed in §9.2, code.claude.com `memory`); the kit's three glob rules exist only as machine symlinks.
- assessment §6 A1: `sync-project.sh` generates and maintains, stamped with `KIT_VERSION` as it already does for `spec-lint/`, `.claude/rules/*.md` with real content (P2-02); done when `sync-project.sh --check` runs in the three repos' CI and fails on divergence.
- kit `platforms/tools/doctor.sh:157-180` symlinks every kit rule into `~/.claude/rules/<plugin>-<rule>.md` unconditionally; once a repo commits `.claude/rules`, Claude Code loads user-level and project-level copies of the same rule on every matching file, paying the tokens twice (P2-02 raises each rule body to up to 40 lines, so the cost is real).
- kit `platforms/tools/sync-project.sh:17-22` already has the "list source/dest pairs, copy, hash-compare" shape; the rules copy reuses it instead of a second generator.

## Current state

kit `platforms/tools/sync-project.sh` (50 lines), the parts this task extends:

```
platforms/tools/sync-project.sh:2: # Syncs the spec validator with a project (a copy, no link to the kit).
platforms/tools/sync-project.sh:3: # Usage: sync-project.sh <repo-dir>           installs/updates .github/spec-lint/
platforms/tools/sync-project.sh:4: #        sync-project.sh --check <repo-dir>   compares with the kit; exit 1 if it diverges
platforms/tools/sync-project.sh:15: hash_file() { shasum -a 256 "$1" | cut -d' ' -f1; }
platforms/tools/sync-project.sh:17: kit_files() { # prints "src rel-dest"
platforms/tools/sync-project.sh:24: if [[ "$MODE" == check ]]; then
platforms/tools/sync-project.sh:25:   FAILED=0
platforms/tools/sync-project.sh:35:   if [[ $FAILED -eq 0 ]]; then echo "sync: $REPO consistent with kit $expected"; else exit 1; fi
platforms/tools/sync-project.sh:40: kit_files | while read -r src rel; do cp "$src" "$DEST/$rel"; done
platforms/tools/sync-project.sh:41: cat "$KIT_DIR/VERSION" > "$DEST/KIT_VERSION"
platforms/tools/sync-project.sh:50: echo "sync: $REPO/.github/spec-lint <- kit $(cat "$KIT_DIR/VERSION")"
```

P2-04 adds `--profile godot|java|docs` (inferred from `project.godot`, `pom.xml` or `docs/spec` when absent) and `profile_plugins()` to this same file (godot = `core`, `dev-core`, `dev-godot`, `quality-core`, `infra-github`; java = `core`, `dev-core`, `dev-java`, `infra-core`, `infra-persistence`, `quality-core`, `quality-security`, `infra-github`; docs = `core`, `architect-core`, `architect-sdd`, `quality-core`, `infra-github`; assessment §6 A1). Read the merged P2-04 script before editing; call `profile_plugins` from `rule_files()`; check mode resolves the profile the same way install mode does (no profile file exists in the repo). If P2-04 is not merged, stop and report the dependency.

kit `platforms/tools/doctor.sh`, the symlink loop to make optional:

```
platforms/tools/doctor.sh:155:   local rule_file
platforms/tools/doctor.sh:157:   for rule_file in "$KIT"/plugins/*/rules/*.md; do
platforms/tools/doctor.sh:162:     destination="$HOME/.claude/rules/$plugin-$name.md"
platforms/tools/doctor.sh:177:       ln -s "$rule_file" "$destination"
platforms/tools/doctor.sh:178:       fix "claude rule symlink created for $plugin-$name"
platforms/tools/doctor.sh:182:   for destination in "$HOME/.claude/rules/"*.md; do
platforms/tools/doctor.sh:186:       "$KIT"/plugins/*/rules/*)
platforms/tools/doctor.sh:187:         if [[ ! -e "$current" ]]; then
```

Kit rules today (three files, each with frontmatter `description`, `trigger: glob`, `globs`, `paths` as YAML sequences): `plugins/dev-godot/rules/godot.md:1-12`, `plugins/dev-java/rules/java.md:1-10`, `plugins/architect-sdd/rules/spec.md:1-8`. Generated names follow `doctor.sh:162`: `dev-godot-godot.md`, `dev-java-java.md`, `architect-sdd-spec.md`.

kit `platforms/tools/smoke.sh:330-337` asserts that doctor created every rule symlink (`fail "Claude rule symlink has the wrong target for $plugin_name-$rule_name"`); it never runs `sync-project.sh`.

kit `README.md:22`, Claude Code row of the "How each agent loads the kit" table, Skills/rules cell: `marketplace plugins and `~/.claude/rules/<plugin>-*.md` symlinks`.

kit `docs/design.md:17`: `- **Zero content copies on the machine.** Agent-facing content is reached through plugin caches or symlinks. This prevents duplicate skill names and drift between installed copies.`

kit `platforms/tools/INDEX.md:7` (doctor row) and `:11`: `| `sync-project.sh` | copies spec validation files into a project; `--check` compares | initialize or refresh project spec CI |`.

kit `docs/projects.md:13`: the `.github/spec-lint/` row of the "what a project receives" table; no row for `.claude/rules/`.

Consumer state (read-only, for grounding; P2-15 applies the sync): stratics-docs has `.claude/skills/review-loop/` and no `.claude/rules/`; stratics-client and stratics-server have no `.claude/` at all. A hand-written file in a consumer's `.claude/rules/` must survive the sync.

## Change

1. kit `platforms/tools/sync-project.sh`: add `rule_files()` next to `kit_files()` (`:17`). It takes the profile's plugin list (P2-04's function) and prints one `src rel-dest` pair per `plugins/<plugin>/rules/*.md`, dest = `.claude/rules/<plugin>-<rule>.md`. Plugins without `rules/` print nothing.
2. Add `render_rule()`: writes the kit rule to a target path as frontmatter copied byte-for-byte (first `---` through closing `---`), then exactly this marker line, then everything after the closing `---` of the kit file unchanged (it already starts with a blank line):

```
<!-- agent-rules-kit: generated from plugins/<plugin>/rules/<rule>.md by platforms/tools/sync-project.sh; kit <VERSION>; do not edit -->
```

   The marker sits after the frontmatter because Claude Code reads `paths:` from the top of the file (verify against code.claude.com/docs/en/memory before relying on it). Output depends only on the kit file and `VERSION`, never on time, hostname or absolute paths.
3. Install mode (after `:43`): `mkdir -p "$REPO/.claude/rules"`; for each pair, render to a temp file; when `cmp -s` differs, `cp` the temp over the destination (0644 like the spec-lint copies); always `rm -f` the temp (idempotent, no mtime churn). Run the not-generated collision check over all pairs before writing anything: if a destination exists and lacks the marker prefix `<!-- agent-rules-kit: generated from `, print `sync: <dest> exists and is not generated; move it by hand` and exit 1 without touching any file. Then delete every `"$REPO/.claude/rules/"*.md` that carries the marker prefix and is not in the current pair list (a plugin removed from the profile); never delete a file without the marker. Extend the final echo (`:50`) with the count of rules written and removed.
4. Check mode (inside the `:24-37` block, before the final verdict): for each pair, render to a temp file and `cmp -s` with the repo copy; report `sync: .claude/rules/<name> missing` or `sync: .claude/rules/<name> diverges from the kit` and set `FAILED=1`; report `sync: .claude/rules/<name> is generated but not in profile` for stale marked files and set `FAILED=1`. Accumulate in `FAILED` the way `:28` does; do not `exit 1` from inside a `while` subshell as `:31-32` do.
5. Update the usage header `:2-4` to name the rules copy and the P2-04 profile argument. bash 3.2: no associative arrays, no `mapfile`, no `${var,,}`; `docs/maintenance.md:54` lists the quoting trap to avoid.
6. kit `platforms/tools/doctor.sh`: in `ensure_claude_links`, wrap `:155-193` so that when `${AI_KIT_USER_RULES:-1}` is `0` the create loop is skipped and every symlink under `~/.claude/rules/` whose target matches `"$KIT"/plugins/*/rules/*` is removed with `fix "removed user-level claude rule symlink <name> (AI_KIT_USER_RULES=0)"`, ending with `ok "user-level claude rules disabled (AI_KIT_USER_RULES=0); repos carry .claude/rules via sync-project.sh"`. Default stays `1`: no behavior change for current machines. Add one comment line above the switch: `# Default flips to 0 once P2-15 lands .claude/rules in the consumer repos.`
7. kit `platforms/tools/smoke.sh`: after `:338` (the `done` that closes the rule-symlink loop started at `:330`), add (a) a doctor run on `$STUB_HOME` with `AI_KIT_USER_RULES=0`, with the same env as `:308-310` (`STUB_EXPOSED=43`), asserting `find "$STUB_HOME/.claude/rules" -type l | wc -l | tr -d ' '` is `0` (the `| tr -d ' '` as `:341` does) and the `ok:` line above is present, then a run with `AI_KIT_USER_RULES=1` restoring the links; (b) a `sync-project.sh` section on a throwaway repo under `$ROOT` containing `AGENTS.md` and `project.godot`, synced with `--profile godot` (the P2-04 profile that enables `dev-godot`): run twice and `fail` if the second run changes any file (`find ... -newer` a stamp file, or compare a `shasum` listing); run `--check` and expect exit 0; append `x` to `.claude/rules/dev-godot-godot.md`, expect `--check` exit 1 and the `diverges` line; create `.claude/rules/my-own.md` without the marker, re-sync with `--profile docs` (does not enable `dev-godot`), expect `dev-godot-godot.md` gone and `my-own.md` intact. Run it from `$SOURCE` so that the fixture, not the live kit, is the source.
8. kit `README.md:22`: Skills/rules cell becomes `marketplace plugins; path rules from the repo's `.claude/rules/<plugin>-<rule>.md` (generated by `sync-project.sh`) or, with `AI_KIT_USER_RULES=1` (default today), `~/.claude/rules/<plugin>-*.md` symlinks`. Add one sentence after the table: a rule present in both places loads twice; set `AI_KIT_USER_RULES=0` before `doctor.sh` on machines whose repos carry `.claude/rules`; the default flips with P2-15.
9. kit `docs/design.md:17`: keep the principle and append to the bullet: `A consumer repository may carry a generated, version-stamped copy of path rules and spec validators (`sync-project.sh`, `--check` detects drift); that copy is a commit, not a machine copy, and it is what cloud sessions, CI runners and new machines load.` Add under "What was left out, and why": `- **A `.devin/rules` copy was left out:** the Devin plugin already loads `plugins/*/rules/` always-on; a second copy would load twice.`
10. kit `platforms/tools/INDEX.md:11`: `copies spec validation files and the profile's path rules (`.claude/rules/`) into a project; `--check` compares`; `:7` doctor row: append `; `AI_KIT_USER_RULES=0` skips user-level rule symlinks`.
11. kit `docs/projects.md`: add a row after `:13`: `| `.claude/rules/<plugin>-<rule>.md` | generated by `sync-project.sh` from `plugins/<plugin>/rules/` for the repo profile, marker line names the source and kit version | path-scoped rules for Claude Code in cloud sessions, CI and new machines |`.
12. kit `CHANGELOG.md` under `## [Unreleased]` / `### Added`: one entry (what, why with assessment §4.2 and §6 A1, proof = the acceptance commands).

## Out of scope

- `CLAUDE.md` and `.claude/settings.json` generation and the profile argument itself: P2-04. Skills vendoring into `.claude/skills/`: P2-06. Running the sync against stratics-docs, stratics-client, stratics-server and adding `--check` to their CI: P2-15.
- Rule content and `RULE_BODY_MAX_LINES`: P2-02. The stale-path gate that also touches `sync-project.sh --check`: P1-01 (rebase on it if it merged first). Hook changes: P1-07, P2-07.
- No `.devin/rules` copy, no change to `plugins/*/rules/*.md`, `rule.schema.json`, `check_kit.py`, `bootstrap.sh`, `refresh.sh` or `plugins/core/AGENTS.md`. Flipping the `AI_KIT_USER_RULES` default stays with P2-15.

## Acceptance criteria

- [ ] `shellcheck platforms/tools/sync-project.sh platforms/tools/doctor.sh platforms/tools/smoke.sh` prints nothing; `bash -n` on the three files exits 0; `ls -l platforms/tools/*.sh` shows `-rwxr-xr-x` on all seven lines.
- [ ] `grep -c 'agent-rules-kit: generated from ' platforms/tools/sync-project.sh` prints at least `2` (render and marker test); `grep -c 'AI_KIT_USER_RULES' platforms/tools/doctor.sh` prints at least `3`; `grep -c 'AI_KIT_USER_RULES=0' platforms/tools/smoke.sh` prints at least `1`.
- [ ] Manual proof, pasted literally in the PR: `r=$(mktemp -d); touch "$r/AGENTS.md"; platforms/tools/sync-project.sh --profile godot "$r"; ls "$r/.claude/rules"` lists exactly `dev-godot-godot.md`; `head -1 "$r/.claude/rules/dev-godot-godot.md"` prints `---`; `grep -c '^<!-- agent-rules-kit: generated from plugins/dev-godot/rules/godot.md' "$r/.claude/rules/dev-godot-godot.md"` prints `1`; `sed -n '/^---$/,/^---$/p' "$r/.claude/rules/dev-godot-godot.md" | diff - <(sed -n '/^---$/,/^---$/p' plugins/dev-godot/rules/godot.md)` prints nothing.
- [ ] Idempotence: `before=$(find "$r/.claude" -type f -exec shasum -a 256 {} + | sort); platforms/tools/sync-project.sh --profile godot "$r"; after=$(...same...); [ "$before" = "$after" ] && echo same` prints `same`.
- [ ] Drift: `echo x >> "$r/.claude/rules/dev-godot-godot.md"; platforms/tools/sync-project.sh --check --profile godot "$r"; echo "exit=$?"` prints a line containing `diverges from the kit` and `exit=1`.
- [ ] Removal safety: `printf 'mine\n' > "$r/.claude/rules/my-own.md"; platforms/tools/sync-project.sh --profile docs "$r"; ls "$r/.claude/rules"` lists `architect-sdd-spec.md` and `my-own.md` and not `dev-godot-godot.md`.
- [ ] Non-generated collision: `printf 'mine\n' > "$r/.claude/rules/architect-sdd-spec.md"; platforms/tools/sync-project.sh --profile docs "$r"; echo "exit=$?"` prints `exit=1` and `cat` shows the file still reads `mine`.
- [ ] `grep -c 'AI_KIT_USER_RULES' README.md docs/design.md platforms/tools/INDEX.md` prints `2`, `0`, `1` respectively (the table cell and the sentence after the table); `grep -c '.claude/rules' docs/projects.md` prints at least `1`; `grep -c 'devin/rules' docs/design.md` prints `1`.
- [ ] Gates, each with its literal last line in the PR: `platforms/tools/check.sh` ends `check: ok`; `platforms/tools/smoke.sh` exits 0; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` ends `OK`; `python3 platforms/ci/validations/check_kit.py --links` reports `3 rules` and no FAIL.
- [ ] `git diff --stat main` lists exactly: `platforms/tools/sync-project.sh`, `platforms/tools/doctor.sh`, `platforms/tools/smoke.sh`, `platforms/tools/INDEX.md`, `README.md`, `docs/design.md`, `docs/projects.md`, `CHANGELOG.md`; `VERSION` untouched; no file under `plugins/`.

## Conventions

- Everything committed is in English; plain ASCII punctuation in new text.
- No layout or path change: the 10.x layout is frozen; `plugins/*/rules/` stays the single source and `~/.claude/rules/<plugin>-<rule>.md` stays the user-level destination; the repo-level copy is a new generated artifact, not a moved one.
- `VERSION` untouched; `CHANGELOG.md` gets a `## [Unreleased]` entry with what, why and proof.
- INDEX.md or README.md of every touched folder lists every entry by name: `platforms/tools/INDEX.md` rows for `sync-project.sh` and `doctor.sh` are updated; `docs/INDEX.md` already lists `design.md` and `projects.md`.
- Every `platforms/**/*.sh` is executable, passes shellcheck and parses under bash 3.2 (`docs/maintenance.md:54`); `smoke.sh` runs with `PATH=/usr/bin:/bin`, so use only tools present under `/usr/bin:/bin` (`cp`, `cmp`, `mv`, `mktemp`, `shasum`, `find`, `grep`, `sed`, `cat`, `cut`, `python3` are all there).
- Rule frontmatter is copied, never rewritten: `description` at most 160 chars, `trigger: glob`, `globs` and `paths` as YAML sequences remain exactly as the kit file has them.
- Claude-specific part: the `.claude/rules` destination and the `paths:` key are Claude Code behavior; the executor may be Devin or Claude Code and needs no Claude-only tool.
- Commit: Conventional Commits, e.g. `feat(sync): generate .claude/rules from the profile's kit rules; AI_KIT_USER_RULES switch in doctor` with `Refs: docs/plans/2026-10-kit-assessment/assessment.md §4.2, §6 A1`.
- PR body = What / Why / How I tested (literal output of the manual proof and the four gates) / Refs.

## Report back

Final message format: `done` (every file path edited; the manual proof commands and the four gate commands with their literal last lines) · `unverified` (anything not run; `claude plugin validate` is skipped when `claude` is not in PATH, which `check.sh:23` reports; `shellcheck` or bash 3.2 when not installed) · `next step` (P2-06 vendors skills with the same marker idea; P2-15 runs the sync in the three repos, adds `--check` to their CI and flips `AI_KIT_USER_RULES` to `0` by default).

Proposed CHANGELOG line (under `### Added`): `- `sync-project.sh` copies the profile's `plugins/<plugin>/rules/*.md` into `<repo>/.claude/rules/<plugin>-<rule>.md` with a generated marker line (source path, kit version); `--check` reports missing, drifted and stale copies; only marked files are ever removed. `doctor.sh` honours `AI_KIT_USER_RULES=0` to skip user-level rule symlinks so a rule is not loaded twice (default `1` until P2-15). Evidence: assessment §4.2 (cloud sessions and runners load no kit rule) and §6 A1. Proof: smoke cases for idempotence, drift and removal; `check.sh`, `smoke.sh`, unit tests and `check_kit.py --links` green.`
