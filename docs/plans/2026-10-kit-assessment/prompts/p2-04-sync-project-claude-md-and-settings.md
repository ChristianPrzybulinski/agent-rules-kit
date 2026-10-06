# P2-04 — sync-project.sh generates CLAUDE.md and .claude/settings.json per repo profile

Phase: 2 · Repos: kit · Branch to create: feat/p2-04-sync-project-claude-md-and-settings from main · Depends on: P1-01 · Effort: ~5 h

## Goal

Extend `platforms/tools/sync-project.sh` so that, besides `.github/spec-lint/`, it generates and checks two agent-configuration files in the consumer repository, selected by a repo profile (`godot`, `java`, `docs`): a `CLAUDE.md` that imports `AGENTS.md`, and a `.claude/settings.json` that registers the kit marketplace and enables only the plugins that profile uses. Measurable result: after this task, running the script against a throwaway repo with a `project.godot` produces a 2-line `CLAUDE.md` and a `settings.json` with exactly 5 `@ai-kit` entries, running it twice changes nothing (`git status --porcelain` empty on the second run), a hand-written `CLAUDE.md` is never overwritten (exit 1 with a message), and `--check` exits 1 when `enabledPlugins` is edited. Today the three Stratics repos have `AGENTS.md` only and `0` of these files (verified with `ls CLAUDE.md .claude/settings.json` in each: all absent).

## Why

- assessment §4.2: none of the three repositories has `CLAUDE.md` or `.claude/settings.json` with `enabledPlugins`; a Claude Code web session, a GitHub Actions runner or a collaborator without `bootstrap.sh` runs with no global rule, skill or hook. Distribution must be "by commit in the consumer repository" through an extended `sync-project.sh`, not by symlink on one machine.
- assessment §5, plugin row: the kit has 12 plugins but all are installed at user scope through `all`, and no repo declares `enabledPlugins`; verdict "partial: the split exists, selective use does not". Cloud row: cloud sessions and the GitHub Action do not load local plugins, and the Action reads `CLAUDE.md` on every run; verdict "wrong for cloud".
- assessment §6 item A1 prescribes exactly these two files, generated and maintained by `sync-project.sh` with `KIT_VERSION` as it already does for `spec-lint/`, and gives the plugin set per repo (client, server, docs). "Done when a clean clone without `~/.ai-kit` loads the same rules in Claude Code web or on a runner and `sync-project.sh --check` fails on divergence."
- Claude Code docs (code.claude.com/docs/en/memory, read 2026-10-06): "Reading `AGENTS.md` directly requires Claude Code v2.1.277 or later. In some sessions Claude can't read `AGENTS.md`, so import it from a `CLAUDE.md` there instead." The table there lists "A CLAUDE.md that already imports AGENTS.md -> your CLAUDE.md, with AGENTS.md included through the import", and the `claude-md-and-agents-md` mode "skips an AGENTS.md it has already loaded, so one that your CLAUDE.md imports is not read twice". The import is the safe shape on every version.
- Claude Code docs (code.claude.com/docs/en/settings-reference, read 2026-10-06) give the shapes used below verbatim: `"extraKnownMarketplaces": { "<name>": { "source": { "source": "github", "repo": "<owner>/<repo>" } } }` and `"enabledPlugins": { "<plugin>@<marketplace>": true }`. The settings page adds two limits the generated README must state: the marketplace key "applies only after each teammate trusts the folder", and "the marketplaces and plugins those two keys declare still don't load in a cloud session" (project-scope plugins are for every collaborator's local sessions; cloud coverage comes from P2-05 and P2-06).
- The kit's marketplace name is `ai-kit` (`.claude-plugin/marketplace.json:2`: `"name": "ai-kit",`) and its GitHub coordinates are already a constant in `platforms/tools/bootstrap.sh:7`: `REPOSITORY="ChristianPrzybulinski/agent-rules-kit"`.

## Current state

- kit `platforms/tools/sync-project.sh:2-4` (usage header):
  `# Syncs the spec validator with a project (a copy, no link to the kit).`
  `# Usage: sync-project.sh <repo-dir>           installs/updates .github/spec-lint/`
  `#        sync-project.sh --check <repo-dir>   compares with the kit; exit 1 if it diverges`
- kit `platforms/tools/sync-project.sh:9-13` (argument parsing; `--profile` goes here):
  `MODE="install"`
  `if [[ "${1:-}" == "--check" ]]; then MODE="check"; shift; fi`
  `REPO="${1:?usage: sync-project.sh [--check] <repo-dir>}"`
  `DEST="$REPO/.github/spec-lint"`
- kit `platforms/tools/sync-project.sh:34-36` (end of check mode; P1-01 adds `scan_stale_kit_paths "$REPO" || FAILED=1` after line 34, keep it):
  `  [[ -f "$REPO/.github/workflows/spec-lint.yml" ]] || { echo "sync: spec-lint.yml missing"; FAILED=1; }`
  `  if [[ $FAILED -eq 0 ]]; then echo "sync: $REPO consistent with kit $expected"; else exit 1; fi`
  `  exit 0`
- kit `platforms/tools/sync-project.sh:50` (last line of install mode):
  `echo "sync: $REPO/.github/spec-lint <- kit $(cat "$KIT_DIR/VERSION")"`
- kit `platforms/tools/INDEX.md:11` (P1-01 rewrites this row; merge, do not duplicate):
  `| `sync-project.sh` | copies spec validation files into a project; `--check` compares | initialize or refresh project spec CI |`
- kit `docs/projects.md:13` (the `.github/spec-lint/` row; the two new rows go right after it):
  `| `.github/spec-lint/` | copy generated by `platforms/tools/sync-project.sh` (`check_spec.py` + schemas + `KIT_VERSION`) | local spec validation in the project's CI |`
- kit `platforms/tools/smoke.sh:492` (last line; the new cases go before it and the message gains `sync-project`):
  `printf 'smoke: OK (%s skills, app fallback, cleanup, symlink safety, manifests)\n' "$skill_count"`
- kit `platforms/ci/validations/test_sync_project.py` exists only after P1-01 (new file there, listed in `platforms/ci/validations/INDEX.md`); this task appends tests to it.
- kit `platforms/kits/sdd/init-spec.sh:25` calls the script with no profile: `"$KIT_DIR/platforms/tools/sync-project.sh" "$REPO"`. Inference must keep this call working (it creates `docs/spec/` before the call).
- kit `CHANGELOG.md:5` `## [Unreleased]`, `:7` `### Added`, `:11` `### Changed`: append to these sections.
- Consumer evidence: stratics-client has `project.godot`, stratics-server has `pom.xml`, stratics-docs has `docs/spec/` and neither marker; none has `CLAUDE.md`; stratics-docs already has `.claude/skills/review-loop/SKILL.md`, so `mkdir -p "$REPO/.claude"` must never replace an existing directory.

## Change

1. kit `platforms/tools/sync-project.sh`: parse `--profile <name>` (any position before `<repo-dir>`, valid values `godot|java|docs`, anything else exits 2 with `sync: unknown profile`). When absent, infer in this order, first match wins, and print `sync: profile=<name> (inferred)`:

```bash
infer_profile() { # $1 = repo dir
  if [[ -f "$1/project.godot" ]]; then echo godot
  elif [[ -f "$1/pom.xml" ]]; then echo java
  elif [[ -d "$1/docs/spec" ]]; then echo docs
  else echo "sync: cannot infer profile for $1 (no project.godot, pom.xml or docs/spec); pass --profile godot|java|docs" >&2; return 1
  fi
}
profile_plugins() { # $1 = profile; prints one plugin name per line, in this order
  case "$1" in
    godot) printf '%s\n' core dev-core dev-godot quality-core infra-github ;;
    java)  printf '%s\n' core dev-core dev-java infra-core infra-persistence quality-core quality-security infra-github ;;
    docs)  printf '%s\n' core architect-core architect-sdd quality-core infra-github ;;
  esac
}
```

   Bash 3.2: no associative arrays, no `mapfile`, no `${var,,}`; keep `set -euo pipefail`. Update the usage comment on lines 3-4 to `sync-project.sh [--profile godot|java|docs] [--check] <repo-dir>` and list the generated files.

2. Same file, install mode, after line 50: generate `<repo>/CLAUDE.md` with exactly these two lines (version from `VERSION`, no other content):

```markdown
<!-- generated by agent-rules-kit sync-project.sh v10.1.0; AGENTS.md is the source -->
@AGENTS.md
```

   Rules: if `CLAUDE.md` exists and does not contain the fixed substring `generated by agent-rules-kit sync-project.sh` (grep `-qF`, version-agnostic), print `sync: $REPO/CLAUDE.md exists and is not generated; move its content into AGENTS.md and delete it, then rerun` and exit 1 without touching any file. If `AGENTS.md` is missing, print `sync: $REPO/AGENTS.md missing; the generated CLAUDE.md imports it` and exit 1. Write the file only when the content differs (idempotent, no mtime churn).

3. Same file, install mode: generate `<repo>/.claude/settings.json` through `python3` (available wherever `check_spec.py` runs). Manage only `extraKnownMarketplaces.ai-kit` and the `@ai-kit` entries of `enabledPlugins`; every other key, every non-`@ai-kit` plugin entry and the existing key order are preserved; new keys append at the end; 2-space indent; trailing newline; `ensure_ascii=False`. Plugin names arrive on stdin from `profile_plugins`. Use this verbatim as the heredoc body (`python3 - "$REPO/.claude/settings.json" <<'PY'`):

```python
import json, sys
from collections import OrderedDict
path = sys.argv[1]
plugins = [line.strip() for line in sys.stdin if line.strip()]
try:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh, object_pairs_hook=OrderedDict)
except FileNotFoundError:
    data = OrderedDict()
markets = data.setdefault("extraKnownMarketplaces", OrderedDict())
markets["ai-kit"] = OrderedDict(source=OrderedDict(source="github", repo="ChristianPrzybulinski/agent-rules-kit"))
enabled = data.setdefault("enabledPlugins", OrderedDict())
for key in [k for k in enabled if k.endswith("@ai-kit")]:
    del enabled[key]
for name in plugins:
    enabled[name + "@ai-kit"] = True
text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
try:
    current = open(path, encoding="utf-8").read()
except FileNotFoundError:
    current = None
if current != text:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
```

   A `settings.json` that is not valid JSON makes the script exit 1 with `sync: $REPO/.claude/settings.json is not valid JSON; fix it by hand` (catch `json.JSONDecodeError` and `sys.exit(1)` after printing). For the godot profile on an empty repo the file is exactly:

```json
{
  "extraKnownMarketplaces": {
    "ai-kit": {
      "source": {
        "source": "github",
        "repo": "ChristianPrzybulinski/agent-rules-kit"
      }
    }
  },
  "enabledPlugins": {
    "core@ai-kit": true,
    "dev-core@ai-kit": true,
    "dev-godot@ai-kit": true,
    "quality-core@ai-kit": true,
    "infra-github@ai-kit": true
  }
}
```

4. Same file, check mode (inside the `if [[ "$MODE" == check ]]` block, before the verdict on line 35): `CLAUDE.md` must exist, carry the marker with the kit's current version and have `@AGENTS.md` as its only non-comment line, else `sync: CLAUDE.md missing or diverges (rerun sync-project.sh)` and `FAILED=1`; `.claude/settings.json` must exist and, loaded with `python3 json`, have `extraKnownMarketplaces["ai-kit"]` equal to the object above and the set of keys ending in `@ai-kit` under `enabledPlugins` equal to the profile set with every value `true`, else `sync: .claude/settings.json diverges for profile <name> (missing: a,b; extra: c)` and `FAILED=1`. Check mode never writes.

5. Same file: extend the generated `.github/spec-lint/README.md` (lines 44-49) with one paragraph: `CLAUDE.md` and `.claude/settings.json` at the repo root are generated too; `AGENTS.md` is the source of instructions; the plugins listed in `enabledPlugins` load in each collaborator's local Claude Code after they trust the folder and are not loaded in cloud sessions or the GitHub Action. Final install message: `sync: $REPO <- kit <version> (profile <name>: spec-lint, CLAUDE.md, .claude/settings.json)`.

6. kit `platforms/tools/INDEX.md:11`: one row, merged with P1-01's wording: `| `sync-project.sh` | copies spec validation files into a project and generates `CLAUDE.md` (imports `AGENTS.md`) plus `.claude/settings.json` (kit marketplace, `enabledPlugins` per profile `godot|java|docs`, inferred or `--profile`); `--check` compares all of them and scans the repo's `*.md` for obsolete kit paths | initialize or refresh a project; in the project's CI |`.

7. kit `docs/projects.md`: after line 13 add two rows: `| `CLAUDE.md` | generated by `platforms/tools/sync-project.sh`: a marker comment plus `@AGENTS.md` (`AGENTS.md` stays the single source) | same content on Claude Code before 2.1.277, in the GitHub Action and in cloud sessions |` and `| `.claude/settings.json` | generated by `platforms/tools/sync-project.sh`: `extraKnownMarketplaces.ai-kit` and `enabledPlugins` for the repo profile (`godot`, `java`, `docs`); other keys preserved | each collaborator's local Claude Code loads only the plugins the repo uses |`. In the "What does NOT go to the project" list, append to the `.github/spec-lint/` bullet (line 24 today) that the same sync maintains `CLAUDE.md` and `.claude/settings.json`.

8. kit `platforms/tools/smoke.sh`: before line 492, add a block that creates `"$ROOT/proj"` with `AGENTS.md` and `project.godot`, then: (a) runs `"$KIT_DIR/platforms/tools/sync-project.sh" "$ROOT/proj"` twice, captures `shasum -a 256` of `CLAUDE.md` and `.claude/settings.json` after each run and fails with `fail "sync-project is not idempotent"` on any difference; asserts `grep -c '@ai-kit' "$ROOT/proj/.claude/settings.json"` prints `5`; (b) runs `--check` and expects exit 0; (c) `python3` rewrites `settings.json` with `enabledPlugins["dev-java@ai-kit"] = True` added, then `--check` must exit 1 and print `diverges for profile godot`; (d) in a second dir `"$ROOT/proj2"` with `AGENTS.md`, `pom.xml` and a hand-written `CLAUDE.md` containing `# mine`, the install must exit 1, print `is not generated` and leave `CLAUDE.md` byte-identical (`grep -c '^# mine$'` prints `1`) and `.claude/settings.json` absent. Use `fail` (line 17) for every assertion and add `sync-project` to the final `smoke: OK` message. Add the same four cases to `platforms/ci/validations/test_sync_project.py` (created by P1-01) as `unittest` methods using `subprocess.run(..., capture_output=True, text=True)`; keep the file under 160 lines.

9. kit `CHANGELOG.md` under `## [Unreleased]`: one `### Added` bullet (what: the two generated files and the profile; why: assessment §4.2 and §6 A1, the three Stratics repos ship no `CLAUDE.md` or `settings.json`; proof: the smoke and unittest cases) and one `### Changed` bullet for the `--check` extension and the new usage.

## Out of scope

- `.claude/rules/*.md` generation: P2-05. `.claude/skills/` vendoring and its manifest: P2-06. Do not create either directory.
- Running the sync and committing the generated files in stratics-docs, stratics-client, stratics-server, and wiring `--check` into their CIs: P2-15. This task only ships the generator; test it on throwaway dirs and, read-only, against local checkouts.
- The stale-kit-path scan, `test_sync_project.py` creation and the `INDEX.md` row text of P1-01: merge onto them, do not rewrite them.
- Hooks in `settings.json` (`PostToolUse` format/lint): P2-07. Removing `~/Documents/GitHub/...` and other machine facts from `docs/projects.md:3`: P2-01.
- `plugins/all`, the marketplace manifests, `bootstrap.sh`, `doctor.sh`, `VERSION`: untouched.

## Acceptance criteria

- [ ] `shellcheck platforms/tools/sync-project.sh platforms/tools/smoke.sh` exits 0; `bash -n` on both exits 0; `test -x platforms/tools/sync-project.sh` exits 0. If a macOS `/bin/bash` 3.2 is available, `/bin/bash -n platforms/tools/sync-project.sh` exits 0.
- [ ] `d=$(mktemp -d); touch "$d/AGENTS.md" "$d/project.godot"; platforms/tools/sync-project.sh "$d"` prints `sync: profile=godot (inferred)`; `wc -l < "$d/CLAUDE.md"` prints `2`; `grep -c '^@AGENTS.md$' "$d/CLAUDE.md"` prints `1`; `grep -c '@ai-kit' "$d/.claude/settings.json"` prints `5`.
- [ ] Same dir: `platforms/tools/sync-project.sh --profile java "$d"` then `grep -c '@ai-kit' "$d/.claude/settings.json"` prints `8` and `grep -c 'dev-godot' "$d/.claude/settings.json"` prints `0` (profile switch replaces the `@ai-kit` set, nothing else).
- [ ] Same dir: `printf '{\n  "permissions": {"allow": ["Bash(ls:*)"]}\n}\n' > "$d/.claude/settings.json"; platforms/tools/sync-project.sh --profile docs "$d"; python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(list(d))" "$d/.claude/settings.json"` prints `['permissions', 'extraKnownMarketplaces', 'enabledPlugins']`.
- [ ] Same dir: running `platforms/tools/sync-project.sh --profile docs "$d"` twice in a row and `shasum -a 256 "$d/CLAUDE.md" "$d/.claude/settings.json"` after each run gives identical output; `platforms/tools/sync-project.sh --profile docs --check "$d"` exits 0, and `platforms/tools/sync-project.sh --check "$d"` (inferred godot) exits 1 printing `diverges for profile godot`.
- [ ] `e=$(mktemp -d); touch "$e/AGENTS.md" "$e/pom.xml"; echo '# mine' > "$e/CLAUDE.md"; platforms/tools/sync-project.sh "$e"; echo $?` prints `1` after a line containing `is not generated`; `cat "$e/CLAUDE.md"` still prints `# mine`; `test -e "$e/.claude/settings.json"` exits 1.
- [ ] `f=$(mktemp -d); touch "$f/project.godot"; platforms/tools/sync-project.sh "$f"; echo $?` prints `1` after `AGENTS.md missing`.
- [ ] `g=$(mktemp -d); touch "$g/AGENTS.md"; platforms/tools/sync-project.sh "$g"; echo $?` prints `1` after `cannot infer profile`; with `--profile x` it prints `2` after `unknown profile`.
- [ ] Read-only against local checkouts (if present beside the kit): `platforms/tools/sync-project.sh --check ../stratics-client` prints `sync: profile=godot (inferred)` and `CLAUDE.md missing`, exit 1; same for `../stratics-server` with `java` and `../stratics-docs` with `docs`. No file in those repos changes (`git -C ../stratics-docs status --porcelain` empty).
- [ ] `grep -c '^| `CLAUDE.md`\|^| `.claude/settings.json`' docs/projects.md` prints `2`; `grep -c 'CLAUDE.md' platforms/tools/INDEX.md` prints `1`.
- [ ] Gates: `platforms/tools/check.sh` exit 0; `platforms/tools/smoke.sh` prints `smoke: OK` and the line mentions `sync-project`; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py" -v` ends with `OK` and lists 4 more tests than before this task; `python3 platforms/ci/validations/check_kit.py --links` exit 0.
- [ ] Claude-specific confirmation (do it when the executor is Claude Code, otherwise report it as unverified): in a session opened inside the godot throwaway dir after trusting it, `/plugin` lists the five `@ai-kit` plugins as enabled from marketplace `ai-kit`, and `/memory` shows `CLAUDE.md` with `AGENTS.md` imported. `claude plugin validate` does not validate `settings.json`, so this manual check is the only proof of the key shapes beyond the docs cited in Why.
- [ ] `grep -c 'CLAUDE.md' CHANGELOG.md` is at least `2` higher than on main, all inside `## [Unreleased]`.

## Conventions

- Everything committed is in English; plain ASCII punctuation in new lines.
- No layout or path change (the 10.x layout is frozen; `plugins/`, `platforms/`, `docs/`, manifests and install destinations keep their paths). The generated files live in the consumer repo, not in the kit.
- `VERSION` untouched (no release in this task). The marker and `KIT_VERSION` read it at run time.
- `CHANGELOG.md` gets `## [Unreleased]` entries written with evidence (what, why, proof).
- `INDEX.md` or `README.md` of every touched folder lists every entry by name (a folder never has both): `platforms/tools/INDEX.md`, `platforms/ci/validations/INDEX.md` (already lists `test_sync_project.py` after P1-01), `docs/INDEX.md` already lists `projects.md`.
- Every `platforms/**/*.sh` is executable, passes shellcheck and parses under bash 3.2 (`docs/maintenance.md:54`: no unquoted text after a quoted string inside `"$(...)"`).
- `check_kit.py` validates backtick paths with an extension that start with `platforms/` or `plugins/` in `docs/*.md` and `platforms/**/*.md` (`platforms/ci/validations/check_kit.py:831-835`): every such path you write must exist.
- Conventional Commits with Refs, for example `feat(sync-project): generate CLAUDE.md and .claude/settings.json per repo profile` with `Refs: docs/plans/2026-10-kit-assessment/prompts/p2-04-sync-project-claude-md-and-settings.md`.
- PR body = What / Why / How I tested (literal output of the gates and of the throwaway-dir commands) / Refs; tick the kit's `.github/PULL_REQUEST_TEMPLATE.md` checklist.
- The executor may be Devin or Claude Code; only the `/plugin` and `/memory` confirmation above is Claude-specific.

## Report back

Final message in three blocks: done (every path created or edited; each Acceptance command with its literal output, including the generated `CLAUDE.md` and godot `settings.json` verbatim) · unverified (anything not run: bash 3.2 parse without a macOS shell, the `/plugin` confirmation when the executor is not Claude Code, missing Stratics checkouts) · next step (P2-05 adds `.claude/rules`, P2-06 vendors skills, P2-15 commits the generated files in the three Stratics repos and wires `--check` into their CIs). Also include the proposed one-line CHANGELOG entry, for example: `sync-project.sh` now generates `CLAUDE.md` (marker + `@AGENTS.md`, never overwriting a hand-written one) and `.claude/settings.json` (`extraKnownMarketplaces.ai-kit` + `enabledPlugins` for the `godot|java|docs` profile, inferred or `--profile`, other keys preserved), and `--check` verifies both; proof: smoke and `test_sync_project.py` cases for idempotence, refusal and drift.
