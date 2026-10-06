# P1-04 — Make the Godot movement model a project decision, not a kit default

Phase: 1 · Repos: kit · Branch to create: fix/p1-04-godot-movement-model-project-decision from main · Depends on: none · Effort: ~2 h

## Goal

Stop the kit from prescribing `_physics_process` + `CharacterBody2D.move_and_slide()` as the only way to move an entity. After this task, `plugins/dev-godot/skills/godot-standards/SKILL.md` and `plugins/dev-godot/templates/project-agents-godot-2d.md` say that the movement model is a project decision declared in the repository `AGENTS.md`, with two documented options (A: physics bodies; B: grid/tile-step with a server-authoritative position) and the rule "never mix the two in one entity". Measurable result: `grep -rn 'Use `_physics_process` for physics/movement\|Move a body' plugins/` prints nothing; the Stratics client (tile-step, DGME-002) is described by option B without any client edit; `godot-standards` stays at or under 80 lines and keeps its description, so the plugin `INDEX.md`, the rule file and the description budget do not move.

## Why

- assessment §4.4 (Movement): `godot-standards` and the `project-agents-godot-2d.md` template mandate `_physics_process` + `move_and_slide()`, while the project decided tile movement without physics (DGME-002) and the client `AGENTS.md` says `move_and_slide`/`CharacterBody2D` is not the movement model. The glob rule loads `godot-standards` on every `.gd`, injecting the wrong advice at every edit.
- assessment §6 item D1: movement and physics stop being a default; the skill and the template say "the movement model is a project decision (`AGENTS.md`/DGME); physics (`CharacterBody2D`) or tile step; never both". The health component example stays valid. assessment §8 puts D1 in week 1.
- kit `plugins/dev-godot/rules/godot.md:4-7` triggers on `**/*.gd`, `**/*.tscn`, `**/project.godot` and line 14 says `Load skill `godot-standards``: the contradiction reaches every client session, not only the ones that touch movement.
- stratics-docs `docs/spec/decisions/DGME-002-tile-movement-continuous-world.md:27` decides "server-validated tile steps"; `:29` "The authoritative position uses integer tile coordinates"; `:31` "Client interpolation and reconciliation are presentation behavior; they do not change confirmed tile coordinates"; `:36` "This decision does not introduce continuous physics movement".
- stratics-client `AGENTS.md:10` says "the client predicts at most one tile step and reconciles" and `AGENTS.md:41` says "Move a character -> tile-step, not physics ... `move_and_slide`/`CharacterBody2D` physics is not the movement model". stratics-docs `docs/spec/features/FEAT-011.md:67` (task T2) names the client behaviour: "input → `move_intent`, optimistic step, confirm/correct reconcile on `entity_moved`/`move_rejected`".
- The same default is repeated in kit `platforms/kits/godot/editor_settings_hints.md:9`, a file the Godot kit README points new projects to.

## Current state

- kit `plugins/dev-godot/skills/godot-standards/SKILL.md` (47 lines; description on line 3 must not change):
  `SKILL.md:3` `description: Godot 2D and typed GDScript standards. Use when editing *.gd, *.tscn, project.godot or GDScript scenes. Not for asset import (skill asset-import).`
  `SKILL.md:31` `## 3. Separate scene responsibilities`
  `SKILL.md:33` `- Prefer scene composition and signals over deep inheritance or parent traversal for game rules.`
  `SKILL.md:34` `- Use `_physics_process` for physics/movement and `_process` for visuals; defer mutations that would invalidate a physics iteration.`
  `SKILL.md:35` `- Keep visuals, physics and rules separate; domain state stays in pure classes/autoload services that tests can instantiate without a scene.`
  `SKILL.md:47` `Done when: changed scripts are typed, scene dependencies use composition/signals, rules are testable without nodes, and headless import plus tests pass.`
- kit `plugins/dev-godot/templates/project-agents-godot-2d.md` (87 lines):
  `project-agents-godot-2d.md:8` `- Tests: [GUT | gdUnit4] in `tests/`. Renderer: [Forward+ | Mobile | Compatibility].`
  `project-agents-godot-2d.md:40` `- Move a body → `_physics_process(delta)`; `CharacterBody2D.move_and_slide()`. Visual/animation → `_process(delta)`.`
  `project-agents-godot-2d.md:46` `- Collision → name layers/masks in `project.godot` (`layer_names/2d_physics`); never use magic numbers.`
  `project-agents-godot-2d.md:50-71` the `HealthComponent` example (keep verbatim; `HealthComponent` also appears on line 17 in the structure tree).
  `project-agents-godot-2d.md:83` `- Never: logic in `_process` that belongs in `_physics_process`; `get_parent()` for game logic; editing `.godot/`.`
- kit `platforms/kits/godot/editor_settings_hints.md:9`:
  `- **Movement**: use `_physics_process(delta)` and `move_and_slide()`; do not move physical bodies in `_process`.`
- kit `plugins/dev-godot/INDEX.md:8` repeats the skill description verbatim; it stays unchanged because the description does not change.
- kit `plugins/dev-godot/rules/godot.md` stays unchanged (P2-02 owns rule content).
- kit `CHANGELOG.md:5`: `## [Unreleased]` starts at line 5 and already has `### Added` and `### Changed` headings (on main and on the plan branch); append the bullet under `### Changed`.

## Change

1. kit `plugins/dev-godot/skills/godot-standards/SKILL.md`: replace lines 31-35 (section 3) with this block, verbatim:

```markdown
## 3. Separate scene responsibilities and respect the movement model

- Prefer scene composition and signals over deep inheritance or parent traversal for game rules.
- Keep visuals, physics and rules separate; domain state stays in pure classes/autoload services that tests can instantiate without a scene.
- The movement model is a project decision, declared in the repository `AGENTS.md` (section "Movement model") and its decision record. Read it before writing or reviewing movement code; if it is missing, ask, do not assume physics.
  - Option A, physics bodies: `CharacterBody2D`/`RigidBody2D`, velocity set and `move_and_slide()` called in `_physics_process(delta)`; collision via named layers/masks; visuals and animation in `_process`.
  - Option B, grid/tile-step: the authoritative position is an integer tile coordinate owned by the game rules (the server when online); input becomes a step intent, the client predicts at most one step and reconciles on confirm/reject; presentation tweens or lerps the sprite toward the confirmed tile in `_process`; no `CharacterBody2D`, no `move_and_slide()`, collision read from the same map data the rules validate.
  - Never mix the two in one entity, and never let presentation (tween, lerp, camera) change the authoritative position.
- Defer mutations that would invalidate a physics iteration (`call_deferred`, `set_deferred`) whenever physics bodies are in use.
```

   Resulting file length: 47 - 5 + 9 = 51 lines (limit 80). Do not touch the frontmatter (lines 1-13), sections 1, 2, 4, 5 or the `Done when` line, except: append to the `Done when` line (line 47 today) the clause `, and movement code follows the declared movement model` before the final period.

2. kit `plugins/dev-godot/templates/project-agents-godot-2d.md`. If P1-06 merged first, line 30 became two lines and every number below 30 shifts by +1; match the quoted content, not the number.
   a. Line 8: append, after the final period, the sentence `Movement model: [A physics bodies | B grid/tile-step] (see "Movement model").` Do not touch the rest of the line; the Tests token reads `[GUT | gdUnit4]` today and `[gdUnit4 | GUT]` if P1-05 merged first (keep whichever is there).
   b. Replace line 40 (`- Move a body → ...`) with one pattern line that defers to the new section; keep the file's `→` arrow so the line matches its neighbours:
      `- Move an entity → follow the "Movement model" section below; never mix physics bodies and tile steps in one entity.`
   c. Replace line 46 with: `- Collision → option A: name layers/masks in `project.godot` (`layer_names/2d_physics`), never magic numbers; option B: read collision from the same map data the rules validate; no physics layers for grid entities.`
   d. Insert a new `## Movement model` section between the `## Patterns (condition → action)` section (after the closing fence of the `HealthComponent` example, line 71 today) and `## Git & PR` (line 73 today). Outline, 18 to 20 lines including blank separators (template grows from 87 to about 106 lines; no line limit applies to templates), bracketed placeholders like the rest of the template:
      - one line: `Declared choice: [A | B]. Decision record: [docs/spec/decisions/DGME-nnn-*.md | docs/adr/nnnn-*.md]. Delete the option not chosen.`
      - `### Option A, physics bodies`: 3 bullets: velocity and `move_and_slide()` in `_physics_process(delta)`; animation and visuals in `_process(delta)`; never move a physics body from `_process`.
      - `### Option B, grid/tile-step (server-authoritative when online)`: 4 bullets: authoritative position = integer tile `[Vector2i]` owned by `[server | GameState]`; input -> `[move_intent]` with a direction only, client predicts at most one step and reconciles on `[entity_moved | move_rejected]` (a rejection snaps back); presentation tweens/lerps the sprite toward the confirmed tile in `_process(delta)` and the camera follows the displayed position; `CharacterBody2D`/`move_and_slide()` are not used for grid entities and collision comes from the map data the rules validate.
      - closing line: `Never mix the two models in one entity; presentation never changes the authoritative position.`
   e. Replace line 83 (`- Never: logic in `_process` that belongs in `_physics_process`; ...`) with: `- Never: mix the two movement models in one entity, or let presentation change the authoritative position; `get_parent()` for game logic; editing `.godot/`.`
   f. Keep lines 50-71 (`HealthComponent`) and every other line unchanged. Lines 30-31 (`--headless --quit`, GUT) and line 87 (`docs/design.md`, `docs/adr/`) are owned elsewhere; do not touch them.

3. kit `platforms/kits/godot/editor_settings_hints.md`: replace line 9 with `- **Movement**: declared per project in its `AGENTS.md` (physics bodies or grid/tile-step; see `godot-standards` section 3). When physics bodies are used, move them in `_physics_process(delta)`, never in `_process`.` The folder index `platforms/kits/godot/README.md:8` already lists the file; no index change.

4. kit `CHANGELOG.md`, under `## [Unreleased]` / `### Changed`: one bullet. What: `godot-standards` section 3 and the `project-agents-godot-2d.md` template (plus `editor_settings_hints.md`) no longer prescribe `_physics_process` + `move_and_slide()`; the movement model is declared per project with options A/B and a no-mixing rule. Why: cite assessment §4.4 and §6 D1, stratics-docs DGME-002 and stratics-client `AGENTS.md:41`. Proof: the grep counts from Acceptance criteria and the `wc -l` of `SKILL.md`.

No file is created or deleted. No file in `plugins/dev-godot/rules/`, `plugins/dev-godot/INDEX.md`, `plugins/dev-godot/skills/godot-standards/references/` or any manifest changes.

## Out of scope

- `plugins/dev-godot/rules/godot.md` content and frontmatter: P2-02.
- Test framework lines in the template (`project-agents-godot-2d.md:8` `[GUT | gdUnit4]`, `:31` GUT command) and `ci-godot.yml`: P1-05.
- The boot proof `godot --path . --headless --quit` in `SKILL.md:45`, `project-agents-godot-2d.md:30` and `:81`: P1-06.
- New references for online 2D (authority, codec, prediction details, pitfalls): P3-01. This task writes at most the option B summary above; no new `references/*.md`.
- Applying the filled-in template or any change to stratics-client `AGENTS.md`: P2-15. Do not edit the Stratics repositories.
- Machine-specific facts in `references/godot-4-versions.md` ("installed on this machine"): P2-01.
- The template's `## More` pointers (`docs/design.md`, `docs/adr/`): no owner in this plan; leave as is.

## Acceptance criteria

- [ ] `grep -n 'Use `_physics_process` for physics/movement' plugins/dev-godot/skills/godot-standards/SKILL.md` prints nothing (exit 1).
- [ ] `grep -c 'never mix\|Never mix' plugins/dev-godot/skills/godot-standards/SKILL.md` prints `1`; `grep -c 'Option A\|Option B' plugins/dev-godot/skills/godot-standards/SKILL.md` prints `2`.
- [ ] `wc -l < plugins/dev-godot/skills/godot-standards/SKILL.md` prints a number <= 80 (expected 51).
- [ ] `sed -n 3p plugins/dev-godot/skills/godot-standards/SKILL.md` is byte-identical to main (`git diff main -- plugins/dev-godot/INDEX.md` prints nothing; `python3 platforms/ci/validations/check_kit.py 2>&1 | grep -c 'description budget'` prints `0` and the command exits 0).
- [ ] `grep -n 'Move a body' plugins/dev-godot/templates/project-agents-godot-2d.md` prints nothing; `grep -n 'logic in `_process` that belongs' plugins/dev-godot/templates/project-agents-godot-2d.md` prints nothing.
- [ ] `grep -c '^## Movement model' plugins/dev-godot/templates/project-agents-godot-2d.md` prints `1`; `grep -c '^### Option' plugins/dev-godot/templates/project-agents-godot-2d.md` prints `2`; `grep -c 'HealthComponent' plugins/dev-godot/templates/project-agents-godot-2d.md` prints `2` (unchanged).
- [ ] `grep -c 'move_and_slide' plugins/dev-godot/templates/project-agents-godot-2d.md` prints exactly `2` (the Option A and Option B bullets) and both matches sit inside the `## Movement model` section (check with `grep -n`).
- [ ] `grep -n 'use `_physics_process(delta)` and `move_and_slide()`' platforms/kits/godot/editor_settings_hints.md` prints nothing.
- [ ] `git diff main --stat -- plugins/dev-godot/rules/ plugins/dev-godot/INDEX.md plugins/dev-godot/skills/godot-standards/references/ VERSION` prints nothing.
- [ ] `ls plugins/dev-godot/templates/ | grep -vE '^(INDEX\.md|(spec|doc|project|kit)-[a-z0-9-]+\.md)$'` prints nothing (no template renamed or added).
- [ ] With stratics-client checked out beside the kit: `grep -n 'tile-step' ../stratics-client/AGENTS.md` prints line 41, and nothing in that repository is modified (`git -C ../stratics-client status --porcelain` prints nothing).
- [ ] Gates: `platforms/tools/check.sh` exit 0; `platforms/tools/smoke.sh` prints `smoke: OK`; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` ends with `OK`; `python3 platforms/ci/validations/check_kit.py --links` exit 0. If `check_kit.py` fails only on files under `docs/plans/`, paste the FAIL lines in the PR body as a pre-existing blocker and do not edit those files.
- [ ] `grep -c 'movement model' CHANGELOG.md` prints at least `1`, inside `## [Unreleased]`.

## Conventions

- Everything committed is in English; plain ASCII punctuation in new lines, except the `→` arrow that the template's pattern lines already use.
- No layout or path change: the 10.x layout is frozen; `plugins/`, `platforms/`, `docs/`, manifests and install destinations keep their paths. Nothing is renamed, created or deleted.
- `VERSION` untouched (no release in this task).
- `CHANGELOG.md` gets a `## [Unreleased]` entry written with evidence (what, why, proof).
- `INDEX.md` or `README.md` of every touched folder lists every entry by name: `plugins/dev-godot/INDEX.md` and `platforms/kits/godot/README.md` already list the touched files; no edit needed there.
- Skill description stays 40-160 chars in the form "<what>. Use when <trigger>. Not for <neighbor> (skill <x>)." and is copied verbatim in `plugins/dev-godot/INDEX.md`; do not change it. All skill descriptions together <= 7,200 chars (6,805 today, measured over `plugins/*/skills/*/SKILL.md`).
- `SKILL.md` <= 80 lines (`check_kit.py` counts the whole file, frontmatter included, `SKILL_MAX_LINES = 80`).
- Templates named `^(spec|doc|project|kit)-[a-z0-9-]+\.md$` (`check_kit.py:694`); `project-agents-godot-2d.md` keeps its name.
- `check_kit.py:832` validates backtick paths with an extension in `plugins/*/templates/*.md` and `platforms/**/*.md`: write the decision-record placeholder in the template as `[docs/spec/decisions/DGME-nnn-*.md | docs/adr/nnnn-*.md]` (the regex only matches paths starting with `../`, `./`, `references/`, `templates/`, `platforms/` or `plugins/`, so a `docs/...` placeholder is never checked; keep the placeholder out of backticks anyway, since it is a bracketed choice and not a path).
- Conventional Commits with Refs, for example `fix(dev-godot): movement model is a project decision, not a kit default` and `Refs: docs/plans/2026-10-kit-assessment/prompts/p1-04-godot-movement-model-not-default.md`.
- PR body = What / Why / How I tested (literal output of the gates and the greps above) / Refs; tick the kit's `.github/PULL_REQUEST_TEMPLATE.md` checklist.
- The executor may be Devin or Claude Code; nothing here needs Claude-specific tools.

## Report back

Final message in three blocks: done (the three edited files plus `CHANGELOG.md`, every command from Acceptance criteria with its literal result, `wc -l` of `SKILL.md`) · unverified (anything not run, for example the stratics-client grep when no checkout exists beside the kit, or `claude plugin validate` when `claude` is not in PATH) · next step (P1-05 and P1-06 fix the test and boot-proof lines in the same two files; P2-15 regenerates the Stratics client `AGENTS.md` from the template; P3-01 adds the option B references). Also include the proposed one-line CHANGELOG entry, for example: `godot-standards` section 3, the `project-agents-godot-2d.md` template and `editor_settings_hints.md` no longer prescribe `_physics_process` + `move_and_slide()`; the movement model is declared per project in `AGENTS.md` (option A physics bodies, option B grid/tile-step with a server-authoritative position, prediction of at most one step and tween/lerp presentation in `_process`), never mixed in one entity (assessment §4.4, §6 D1; stratics-docs DGME-002).
