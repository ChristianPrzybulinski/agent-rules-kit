# P2-10 — Move non-core skills to an optional extras plugin

Phase: 2 · Repos: kit (agent-rules-kit) · Branch to create: feat/p2-10-extras-plugin from main · Depends on: P2-09 (it rewrites `plugins/core/INDEX.md`, `plugins/dev-core/INDEX.md` and root `INDEX.md:24`; apply this prompt on top of its result so the two edits do not collide) · Effort: ~3 h

## Goal

Create `plugins/extras`, a content plugin that requires `core` and is NOT pulled in by the `all` bundle, and move five skills into it with `git mv`: `find-skills` and `skill-creator` (from `plugins/core`), `frontend-design` (from `plugins/dev-core`), `krita` (from `plugins/dev-godot`) and `dbeaver` (from `plugins/infra-persistence`). Measurable result: a default install (`all`) exposes 38 skills instead of 43 (34 instead of 39 after P2-09) and 1,112 fewer description characters (303 + 319 + 204 + 142 + 144) to the model's skill selector; the kit total stays 6,803 characters, because moving a skill between plugins changes nothing in the sum computed by `check_kit.py:639`; all four kit gates stay green and `vendor.sh --check` prints `vendor: lock consistent`.

## Why

- assessment §4.7: `find-skills` (vendored) carries a 303-character description, above the 160 cap of the kit's own schema, and "instructs installing third-party skills by popularity, a prompt injection vector that contradicts the kit's security posture" (assessment.md:165); `frontend-design` is for the web and Godot game UI does not benefit; `krita` and `dbeaver` describe GUI use by humans and "cost description budget with no gain for the agent".
- assessment §6 F2 (authoritative shape): move `frontend-design`, `find-skills`, `krita`, `dbeaver`, `skill-creator` to an optional plugin `extras`; `skill-creator` "is useful for the maintainer, not for the executor"; none of the five helps implement a Stratics task.
- Measured on branch `claude/modest-mendel-7tq8a4` (v10.1.0): 43 skills, description total 6,803 of the 7,200 budget (`check_kit.py:25`); the five skills account for 1,112 of those characters; `find-skills/SKILL.md` is 141 lines and `skill-creator/SKILL.md` 485 lines, both exempt from the 80-line cap only because `VENDOR.md` exists (`check_kit.py:579-581`, `:614-618`).
- `plugins/all` is required to depend on every content plugin by `check_kit.py:296-298`, and the root meta-plugin requires `all` (`.devin-plugin/plugin.json:5-11`, README.md:35-38), so today there is no way to ship a plugin that a default install skips. An opt-in plugin needs one validator exception, documented.
- Only one place hardcodes the plugin count: `smoke.sh:468` `assert len(plugin_dirs) == 12`; `bootstrap.sh:139`, `refresh.sh:107` and `doctor.sh:489` iterate `"$KIT"/plugins/*/`; `smoke.sh:175-177` globs `plugins/*/skills`. The only literal counts are the words `twelve` in README.md:3 and README.md:53 (INDEX.md:31 says `twelve-factor`, unrelated).

## Current state

Line numbers were measured on v10.1.0 before P2-09; after P2-09 `skill-creator` is `plugins/core/INDEX.md:10`. Match rows by the quoted content, never by number.

Skill folders to move (every path exists today):
- `plugins/core/skills/find-skills/` (SKILL.md, VENDOR.md) and `plugins/core/skills/skill-creator/` (SKILL.md, VENDOR.md, LICENSE.txt, agents/, assets/, eval-viewer/, references/, scripts/).
- `plugins/dev-core/skills/frontend-design/` (SKILL.md, VENDOR.md, LICENSE.txt).
- `plugins/dev-godot/skills/krita/` and `plugins/infra-persistence/skills/dbeaver/` (SKILL.md, agents/openai.yaml; both user-only: `triggers: [user]`, `disable-model-invocation: true`, `allow_implicit_invocation: false`).

Index rows that leave their plugin (the whole row is removed; descriptions are copied verbatim into the new index):
- `plugins/core/INDEX.md:7`: `| `find-skills` | Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending capabilities. This skill should be used when the user is looking for functionality that might exist as an installable skill. |`
- `plugins/core/INDEX.md:12`: `| `skill-creator` | Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy. |`
- `plugins/dev-core/INDEX.md:9`: `| `frontend-design` | Guidance for distinctive, intentional visual design when building new UI or reshaping an existing one. Helps with aesthetic direction, typography, and making choices that don't read as templated defaults. |`
- `plugins/dev-godot/INDEX.md:9`: `| `krita` | Krita pixel-art workflow. Use when editing pixel art, retouching sprites or defining sprite export. Not for Godot import (skill asset-import). |`
- `plugins/infra-persistence/INDEX.md:7`: `| `dbeaver` | DBeaver GUI inspection. Use when inspecting a database, exporting test data or drawing an ER diagram. Not for schema changes (skill postgresql). |`

Lock and validator:
- `platforms/kits/third-party/skills.lock:3`: `skill-creator | core | anthropics/skills | ...`; `:4`: `find-skills | core | vercel-labs/skills | ...`; `:5`: `frontend-design | dev-core | anthropics/skills | ...`; `:2` `grilling | architect-core | ...` stays.
- `platforms/ci/validations/check_kit.py:31`: `BUNDLE_PLUGIN = "all"`; `:216`: `content_plugins = {name: path for name, path in plugins.items() if name != BUNDLE_PLUGIN}`; `:296-298`: `if dep_graph[name] != sorted(content_plugins): fail(..., "'all' must require every content plugin")`; `:340-345`: `optionalPlugins must list every plugin except 'all'` (this one already wants `extras` listed; no change); `:899-909`: lock plugin column must equal the skill's owning plugin and `VENDOR.md` must carry the lock sha.

Manifests and docs that gain or lose a line:
- `plugins/all/.devin-plugin/plugin.json:6-62` (`requiredPlugins`, 11 entries), `plugins/all/.claude-plugin/plugin.json:8-20` (`dependencies`, 11 names), `plugins/all/INDEX.md:7` (the "Depends on" cell): dependency lists unchanged; only the description string changes.
- `.devin-plugin/plugin.json:12-68` `optionalPlugins` (11 entries, alphabetical); `.claude-plugin/marketplace.json:12-97` `plugins` (12 entries, `all` last); `.agents/plugins/marketplace.json:6-151` `plugins` (12 entries, every policy `INSTALLED_BY_DEFAULT`).
- Plugin descriptions that name a moved skill: `plugins/core/plugin.json:5`, `plugins/core/.devin-plugin/plugin.json:4`, `plugins/core/.claude-plugin/plugin.json:4`, `.claude-plugin/marketplace.json:16`: `ai-kit core: always-on global rules, session discipline and kit-authoring skills`; `plugins/infra-persistence/plugin.json:5`, `.devin-plugin/plugin.json:4`, `.claude-plugin/plugin.json:4`, `.claude-plugin/marketplace.json:79`: `ai-kit persistence: PostgreSQL, Redis and DBeaver`.
- Root `INDEX.md:12`: `| [`plugins/`]\(plugins/) | plugin family: core, satellites and the `all` bundle |`; `:23` Content cell `always-on rules, hook guard, session and kit-authoring skills`; `:26` `... Godot 2D, asset import, Krita`; `:32` `... PostgreSQL, Redis, DBeaver`; `:34`: `| [`plugins/all/`]\(plugins/all/INDEX.md) | all above | manifest-only bundle: install everything |`.
- README.md:3 `twelve focused plugins with shared manifests`; README.md:39 `devin plugins install ChristianPrzybulinski/agent-rules-kit#plugins/dev-java  # one satellite + its chain`; README.md:53 `The root marketplace catalog lists all twelve plugins`; README.md:59 `claude plugin install all@ai-kit    # or a single satellite; dependencies resolve automatically`.
- docs/design.md:9: `The `all` bundle is manifest-only and resolves to every plugin.`; docs/maintenance.md:18 ends `...and `.agents/plugins/marketplace.json`; add it to `all`'s manifests |`.
- New files: `plugins/extras/INDEX.md`, `plugins/extras/plugin.json`, `plugins/extras/.devin-plugin/plugin.json`, `plugins/extras/.claude-plugin/plugin.json` (new files; the plugin is listed by root `INDEX.md` Plugins table and by the three root catalogs above).

## Change

Decision, taken here and to be recorded in CHANGELOG and docs: `extras` stays OUT of `all`. `all` is the default install (README.md:35-38 and :59) and the point of the move is to take the five descriptions out of what the model sees by default; keeping `extras` in `all` would move folders and change nothing. The validator rule at `check_kit.py:296-298` is relaxed by a named exception, not removed.

1. Move the folders (kit), preserving history and the vendored `VENDOR.md`/`LICENSE.txt` files unchanged: `git mv plugins/core/skills/find-skills plugins/extras/skills/find-skills`, same for `plugins/core/skills/skill-creator`, `plugins/dev-core/skills/frontend-design`, `plugins/dev-godot/skills/krita`, `plugins/infra-persistence/skills/dbeaver` (create `plugins/extras/skills/` first). Edit no SKILL.md: the vendored ones are regenerated by `vendor.sh`, and `krita`/`dbeaver` already satisfy the kit schema (35 lines, descriptions of 142 and 144 chars).
2. Create `plugins/extras/plugin.json` (kit, new file), the same shape as `plugins/core/plugin.json`:
   ```json
   {
     "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
     "name": "extras",
     "version": "10.1.0",
     "description": "ai-kit extras: opt-in skills outside the default install (frontend-design, krita, dbeaver, find-skills, skill-creator)"
   }
   ```
   Create `plugins/extras/.devin-plugin/plugin.json` (new file) with `name`, `version`, the same `description` and `"requiredPlugins": [{"source": "git-subdir", "url": "https://github.com/ChristianPrzybulinski/agent-rules-kit.git", "path": "plugins/core"}]` (copy the entry shape from `plugins/dev-core/.devin-plugin/plugin.json:5-11`). Create `plugins/extras/.claude-plugin/plugin.json` (new file) with `name`, `version`, `description`, the `author` block from `plugins/dev-core/.claude-plugin/plugin.json:5-7` and `"dependencies": ["core"]`. `check_kit.py:290-291` requires the Devin and Claude dependency sets to be identical.
3. Create `plugins/extras/INDEX.md` (kit, new file), following `plugins/infra-persistence/INDEX.md` line for line: the heading in the same `# <name>/ ... ai-kit extras ... opt-in skills` pattern (keep the dash character the other indexes use), one sentence `Opt-in plugin: not required by the `all` bundle; install it explicitly (see README).`, a `## `skills/`` table with the five rows `| `dbeaver` | ... |`, `| `find-skills` | ... |`, `| `frontend-design` | ... |`, `| `krita` | ... |`, `| `skill-creator` | ... |` in that order, each description byte-for-byte from the SKILL.md frontmatter (`check_kit.py:788-792` compares them), and the closing `Manifests:` line copied from `plugins/infra-persistence/INDEX.md:11`.
4. Remove the five rows listed in Current state from `plugins/core/INDEX.md`, `plugins/dev-core/INDEX.md`, `plugins/dev-godot/INDEX.md`, `plugins/infra-persistence/INDEX.md` (kit). Leave `asset-import`'s description untouched: its `Not for drawing art (skill krita)` still names an existing skill, and appending `, plugin extras` would push it past 160 characters.
5. Edit `platforms/kits/third-party/skills.lock:3-5` (kit): the plugin column becomes `extras` on the `skill-creator`, `find-skills` and `frontend-design` lines; line 2 (`grilling | architect-core`) is unchanged. Run `platforms/tools/vendor.sh --check` (no network needed in check mode; it reads `plugins/extras/skills/<name>/VENDOR.md`).
6. Edit `platforms/ci/validations/check_kit.py` (kit). Line numbers refer to the file before any edit; apply the edits bottom-up (296-298 first, then 216, then 31) or locate them by the quoted content. After line 31 add:
   ```python
   OPTIONAL_PLUGINS = {"extras"}  # opt-in content plugins that the 'all' bundle does not require
   ```
   Replace lines 296-298 with:
   ```python
           expected = sorted(set(content_plugins) - OPTIONAL_PLUGINS)
           if dep_graph[name] != expected:
               fail(rel(plugin_dir / ".devin-plugin/plugin.json"),
                    f"'all' must require every content plugin except opt-in {sorted(OPTIONAL_PLUGINS)}")
   ```
   After line 216 add a guard so a typo in the set is caught: `for optional in sorted(OPTIONAL_PLUGINS - plugins.keys()): fail("plugins", f"OPTIONAL_PLUGINS names '{optional}', which is not a plugin directory")`. Do not touch lines 340-345: `optionalPlugins` must still list every plugin except `all`, including `extras`.
7. Register the plugin (kit): `.devin-plugin/plugin.json` gets a seventh `optionalPlugins` entry `"path": "plugins/extras"` between `plugins/dev-java` (:38-42) and `plugins/infra-core` (:43-47), same `source`/`url` as its neighbours; `.claude-plugin/marketplace.json` gets, before the `all` entry (:90-96), `{"name": "extras", "source": "./plugins/extras", "description": "<the description from step 2>", "version": "10.1.0", "category": "productivity"}`; `.agents/plugins/marketplace.json` gets, before the `all` entry (:139-150), an object identical in shape to `:115-126` with `"name": "extras"` and `"path": "./plugins/extras"`. Keep `"installation": "INSTALLED_BY_DEFAULT"`: `check_kit.py:353-364` checks only names and paths, Codex has no dependency resolution, and `bootstrap.sh:139-149` installs every catalog entry one by one anyway; verify against the Codex plugin marketplace documentation before relying on any other policy value. Do NOT add `extras` to `plugins/all/.devin-plugin/plugin.json` or `plugins/all/.claude-plugin/plugin.json`.
8. Edit `plugins/all/INDEX.md` (kit): line 3 becomes `Manifest-only plugin: installs every ai-kit plugin except the opt-in `extras` through dependency resolution. No content of its own.`; after line 3 add `Not included: `extras` (opt-in; install it explicitly).`
9. Plugin descriptions (kit), one string per plugin in all its copies: core becomes `ai-kit core: always-on global rules, session discipline and kit templates` (`plugins/core/plugin.json:5`, `plugins/core/.devin-plugin/plugin.json:4`, `plugins/core/.claude-plugin/plugin.json:4`, `.claude-plugin/marketplace.json:16`); infra-persistence becomes `ai-kit persistence: PostgreSQL and Redis` (`plugins/infra-persistence/plugin.json:5`, its two hidden manifests line 4, `.claude-plugin/marketplace.json:79`); all becomes `ai-kit bundle: installs every ai-kit plugin except the opt-in extras` (`plugins/all/plugin.json:5`, `plugins/all/.devin-plugin/plugin.json:4`, `plugins/all/.claude-plugin/plugin.json:4`, `.claude-plugin/marketplace.json:93`). `dev-core` and `dev-godot` descriptions do not name a moved skill; leave them.
10. Root `INDEX.md` (kit): `:12` Purpose cell becomes `plugin family: core, satellites, the `all` bundle and the opt-in `extras``; `:23` becomes `always-on rules, hook guard, session skills, kit templates`; `:26` drops `, Krita`; `:32` becomes `PostgreSQL, Redis`; `:34` Requires cell becomes `all above except `extras`` and its Content cell becomes `manifest-only bundle: install everything except `extras``; insert after `:33` a row in the same format as its neighbours: first cell is a markdown link whose text is `plugins/extras/` and whose target is `plugins/extras/INDEX.md` (relative to the root `INDEX.md`; never write that link inside this prompt file, the kit link check would resolve it from here), Requires cell `core`, Content cell `opt-in: frontend-design, krita, dbeaver, find-skills, skill-creator (not in `all`)`; append to Invariants (`:59-65`) the line `- `plugins/all/` requires every content plugin except the opt-in `extras`; `check_kit.py` `OPTIONAL_PLUGINS` is the single list of opt-in plugins.` If P2-09 already rewrote `:23`/`:24`, change only the words named here.
11. README.md (kit): `:3` `twelve focused plugins` becomes `thirteen plugins (twelve in the default `all` bundle plus the opt-in `extras`)`; after `:39` add `devin plugins install ChristianPrzybulinski/agent-rules-kit#plugins/extras   # opt-in extras (not in all)`; `:53` `all twelve plugins` becomes `all thirteen plugins`; after `:59` add `claude plugin install extras@ai-kit  # opt-in: frontend-design, krita, dbeaver, find-skills, skill-creator`. Add one sentence after `:53` (end of the Codex section): `On Codex, bootstrap installs every catalog entry including `extras`; remove it afterwards if unwanted (verify the exact `codex plugin` subcommand against the Codex CLI help before writing it).`
12. docs/design.md:9 (kit): the sentence becomes `The `all` bundle is manifest-only and resolves to every plugin except the opt-in `extras` (frontend design, Krita, DBeaver, skill discovery and skill authoring), which is installed explicitly.` docs/maintenance.md:18: replace the ending `add it to `all`'s manifests` with `add it to `all`'s manifests, unless it is opt-in: then add its name to `OPTIONAL_PLUGINS` in `platforms/ci/validations/check_kit.py` instead`.
13. CHANGELOG.md (kit) under `## [Unreleased]`: in `### Added` the bullet for `plugins/extras`; in `### Changed` one bullet for the validator exception and the lock plugin column. Each bullet carries what, why (assessment §4.7 and §6 F2) and proof (the literal `check_kit.py` and `vendor.sh --check` output lines). State explicitly: `description budget unchanged at 6,803 chars; the default install now carries 1,112 chars less`.
14. Edit `platforms/tools/smoke.sh:468` (kit): `assert len(plugin_dirs) == 12` becomes `assert len(plugin_dirs) == 13`; nothing else in the script changes.

## Out of scope

- Renaming or merging any skill (P2-09 owns `clean-code`/`simplicity`/`sessions` and friends); simplifying `tokens` (P2-11); shortening the vendored descriptions of `find-skills` (303) and `skill-creator` (319) past the 160 cap, which stay vendor-exempt (`check_kit.py:580-581`).
- Any change to `bootstrap.sh`, `refresh.sh`, `doctor.sh` and the rest of `smoke.sh` beyond line 468: their `plugins/*/` loops already cover a thirteenth plugin; making Codex skip `extras` would need a hardcoded name in three scripts and the doctor fallback symlinks (`doctor.sh:254`) would still expose the skills; record this limit in README (step 11), do not solve it here.
- `sync-project.sh` vendoring choices for projects (P2-06); the stale-path gate (P1-01); machine-specific facts in docs (P2-01).
- A VERSION bump or a release.

## Acceptance criteria

- [ ] `ls plugins/extras/skills` prints `dbeaver find-skills frontend-design krita skill-creator`; `ls plugins/core/skills plugins/dev-core/skills plugins/dev-godot/skills plugins/infra-persistence/skills | grep -c -E '^(find-skills|skill-creator|frontend-design|krita|dbeaver)$'` prints `0`.
- [ ] `ls plugins/extras plugins/extras/.devin-plugin plugins/extras/.claude-plugin` shows `INDEX.md`, `plugin.json`, `skills` and the two hidden `plugin.json` files; `python3 -c "import json;[json.load(open(p)) for p in ['plugins/extras/plugin.json','plugins/extras/.devin-plugin/plugin.json','plugins/extras/.claude-plugin/plugin.json']]"` exits 0.
- [ ] `grep -c '^| `' plugins/extras/INDEX.md` prints `5`; `platforms/ci/validations/check_kit.py` reports no `description differs from frontmatter` line.
- [ ] `grep -c '| extras |' platforms/kits/third-party/skills.lock` prints `3`; `grep -c '| architect-core |' platforms/kits/third-party/skills.lock` prints `1`; `platforms/tools/vendor.sh --check` prints `vendor: lock consistent` and exits 0.
- [ ] `grep -c 'plugins/extras' plugins/all/.devin-plugin/plugin.json` prints `0` and `grep -c '"extras"' plugins/all/.claude-plugin/plugin.json` prints `0`; `grep -c 'plugins/extras' .devin-plugin/plugin.json` prints `1`; `grep -c '"extras"' .claude-plugin/marketplace.json .agents/plugins/marketplace.json` prints `1` for each.
- [ ] `grep -c 'OPTIONAL_PLUGINS' platforms/ci/validations/check_kit.py` prints `4`; `grep -c "sorted(content_plugins)" platforms/ci/validations/check_kit.py` prints `0`.
- [ ] `grep -c 'len(plugin_dirs) == 13' platforms/tools/smoke.sh` prints `1`.
- [ ] `grep -rn -E 'find-skills|skill-creator|frontend-design' plugins/core plugins/dev-core` prints 0 lines; `grep -c 'krita' plugins/dev-godot/INDEX.md` prints `1` (the `asset-import` pointer); `grep -c -i 'dbeaver' plugins/infra-persistence/INDEX.md plugins/infra-persistence/plugin.json` prints `0` for both.
- [ ] `grep -c 'twelve' README.md` prints `1` (the parenthetical in line 3 only); `for f in README.md INDEX.md docs/design.md docs/maintenance.md CHANGELOG.md; do grep -q 'extras' "$f" || echo "missing: $f"; done` prints nothing.
- [ ] Description total unchanged: `python3 -c "import re,glob;print(sum(len(re.search(r'^description:\s*(.*)$',open(f).read(),re.M).group(1).strip().strip('\"\'')) for f in glob.glob('plugins/*/skills/*/SKILL.md')))"` prints the same number before and after this change on the same base commit (6803 on v10.1.0; lower if P2-09 merged first).
- [ ] Gates: `platforms/tools/check.sh` exits 0 and `python3 platforms/ci/validations/check_kit.py | tail -1` starts with `check: OK (13 plugins, 43 skills,` (`39 skills` after P2-09); `platforms/tools/smoke.sh` exits 0; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` prints `OK`; `python3 platforms/ci/validations/check_kit.py --links` exits 0.
- [ ] `git diff --stat main -- VERSION` prints nothing; `git diff --name-status main | grep '^R'` lists the five moved folders as renames.

## Conventions

- Markdown links quoted from existing files in this prompt are written with an escaped parenthesis (`]\(`) so the kit link check does not resolve them from this folder; in the real files they are plain `](`. Match and write them without the backslash.
- Everything committed is in English; plain ASCII punctuation in new text, except the em dash in the `plugins/extras/INDEX.md` H1 which mirrors the other plugin indexes.
- No layout or path change beyond adding `plugins/extras/`: the 10.x layout is frozen; `plugins/`, `platforms/`, `docs/`, manifests and install destinations keep their paths. `plugins/extras` holds only entries from `ALLOWED_PLUGIN_ENTRIES` (`check_kit.py:196-199`).
- VERSION untouched; every manifest keeps `"version": "10.1.0"` (or the current VERSION value if it moved).
- `CHANGELOG.md` gets `## [Unreleased]` entries written with evidence (what, why, proof).
- `INDEX.md` of every touched folder lists every entry by name (a folder never has both INDEX.md and README.md); plugin `INDEX.md` tables carry the skill description verbatim.
- All skill descriptions together <= 7,200 chars (6,803 today); vendored skills keep their `VENDOR.md` and are exempt from the 160-char and 80-line caps; non-vendored SKILL.md <= 80 lines.
- User-only skills (`krita`, `dbeaver`) keep `triggers: [user]` + `disable-model-invocation: true` + `agents/openai.yaml` with `policy.allow_implicit_invocation: false`; allowed-tools stay lowercase.
- Every `platforms/**/*.sh` stays executable, passes shellcheck and parses under bash 3.2 (only `smoke.sh:468` is edited here; confirm with `git diff --name-only main -- platforms/tools` printing exactly `platforms/tools/smoke.sh`, and `shellcheck platforms/tools/smoke.sh` exiting 0).
- Conventional Commits with Refs (`feat(plugins): add opt-in extras plugin for non-core skills` / `Refs: assessment §4.7, §6 F2`); PR body = What / Why / How I tested (literal output) / Refs.

## Report back

Final message in this format:
- done: list of paths created, edited and moved (kit-relative), then the commands run with their literal results: `platforms/tools/check.sh` last line, `platforms/tools/smoke.sh` last line, the unittest `OK` line, `check_kit.py --links` exit code, `vendor.sh --check` output, the description-total one-liner output before and after.
- unverified: anything not run (for example `claude plugin install extras@ai-kit` on a real machine, Codex marketplace policy values, the exact `codex plugin` subcommand that removes an installed plugin), each with the command the maintainer should run.
- next step: P2-11 (tokens) or P2-06 (sync-project vendoring), and whether `OPTIONAL_PLUGINS` should gain a schema-level home in a later prompt.
- Proposed CHANGELOG line: `- `plugins/extras` (requires `core`, not in `all`): `find-skills`, `skill-creator`, `frontend-design`, `krita`, `dbeaver` moved out of the default install; `check_kit.py` `OPTIONAL_PLUGINS` exempts opt-in plugins from the "'all' requires every content plugin" rule; lock plugin column updated. Evidence: assessment §4.7/§6 F2; default install drops 5 skills and 1,112 description chars, kit total unchanged at 6,803; check.sh, smoke.sh, unittest and vendor.sh --check green.`
