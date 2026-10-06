# P3-10 — progress.json harness for long implementations

Phase: 3 · Repos: kit · Branch to create: feat/p3-10-progress-json-harness from main · Depends on: P1-08 (issue per task, ten-column rows; it rewrites `sdd-tasks` and `sdd-implement`, so anchor on sentences, never on step numbers), P2-08 (derived status is the post-merge source of truth this prompt defers to) · Effort: ~4 h

## Goal

Give every FEAT in implementation one machine-readable progress file, `docs/spec/progress/FEAT-nnn.json`, created by `sdd-tasks` from the task table and updated by `sdd-implement` after each proof, so that a fresh session (Claude Code or Devin) orients itself from that file plus `git log --oneline -20` instead of from a hand-edited Markdown cell. The kit ships the schema (`platforms/ci/schemas/progress.schema.json`), an example (`platforms/kits/sdd/progress.example.json`), validation in `check_spec.py` with unit tests, and the schema copy in `sync-project.sh`. Measurable result: `check_spec.py` rejects a progress file whose `passes` is not a boolean, whose `feat` has no FEAT file or whose name differs from its `feat`; the unit test count rises from 4 to at least 10; `sync-project.sh` installs six schemas instead of five; all four kit gates stay green.

## Why

- assessment §5, harness row: Anthropic prescribes "a feature list in JSON with `passes`, a progress file, commits as checkpoints, read git log + progress at start" (2025-11, 2026-03); the kit has only `session-handoff` in Markdown and a Markdown task table in the FEAT; verdict "partial: Markdown status that nobody updates (§4.6)".
- assessment §7 item N6: one `progress.json` per FEAT in implementation with `passes: true|false` (JSON is edited wrongly less often by the model than Markdown), read at the start of every session together with `git log`; it replaces the manual status in the FEAT for the executor.
- The source is anthropic.com/engineering/effective-harnesses-for-long-running-agents (2025-11, listed in assessment §9.3); verify against that page before quoting any wording from it.
- Measured on stratics-docs 2026-10-06 (P2-08 Why): 128 task rows `todo`, 3 `done`, while 27 task PRs had merged; stratics-docs `docs/spec/features/FEAT-009.md:92-93` hold `| todo |` for T2 and T3 although their PRs merged on 2026-10-05. The Markdown cell is not the executor's state and should not pretend to be.
- Today no kit file knows the word `progress` outside the status enum: `grep -n progress platforms/ci/validations/check_spec.py platforms/tools/sync-project.sh plugins/architect-sdd/skills/*/SKILL.md plugins/core/skills/session-handoff/SKILL.md` matches only `check_spec.py:84` (`in-progress`) and `sdd-implement/SKILL.md:22` (`status: in-progress`).

## Current state

- kit `platforms/ci/validations/check_spec.py:112-117` loads one schema per `STRUCT` key only: `for name in STRUCT:` / `p = schemas_dir / f"{name}.schema.json"`; `:119-127` builds `targets` from `spec.md`, `features`, `requirements`, `decisions`, `debts` (`*.md` only); `:190-192` ends with `if failures: sys.exit(1)` / `print(f"spec: OK ({len(ids)} artifacts)")`. `feats` (`:130`, filled at `:164`) maps every FEAT id to its `requirements` list; `ids` (`:129`) maps id to path.
- kit `platforms/ci/validations/test_check_spec.py:36` `class FeatReqCrossCheckTest(unittest.TestCase):` with `setUp` creating `features/` and `requirements/functional/` (`:38-41`), helpers `feat` (`:46`), `req` (`:49`) and `run_check` (`:53-55`); 4 tests, run by `.github/workflows/ci.yml:28` `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`.
- kit `platforms/tools/sync-project.sh:13` `SCHEMAS="spec feature requirement decision debt"`; `:17-22` `kit_files()` copies `check_spec.py` and one `schemas/$s.schema.json` per entry; `:29-33` `--check` compares hashes of the same list.
- kit `platforms/ci/schemas/INDEX.md:15` `| `debt.schema.json` | `docs/spec/debts/*.md` |` is the last table row; `:17` `Consumed by `../validations/check_kit.py` and `check_spec.py`. Details: `../README.md`.`
- kit `platforms/ci/README.md:16` `| `debt.schema.json` | `docs/spec/debts/*.md` | `DEBT-nnn-slug.md` |`; `:18` `The five spec schemas (`spec`, `feature`, `requirement`, `decision`, `debt`) go to projects **as a copy**: ...`; `:23` `| `validations/check_spec.py` | a project's `docs/spec`: schema + id=prefix + FEAT↔REQ cross-check (...) + unique IDs; self-test `validations/test_check_spec.py` |`.
- kit `platforms/ci/validations/INDEX.md:7` `| `check_spec.py` | a project's `docs/spec/` against `../schemas/` | `check.sh --spec`, the projects' spec-lint workflow |`.
- kit `platforms/kits/sdd/INDEX.md:5` is the only table row (`init-spec.sh`); the folder holds `INDEX.md` and `init-spec.sh`. `check_kit.py:737-762` requires every entry of this folder to appear in its `INDEX.md`.
- kit `platforms/ci/schemas/debt.schema.json:1-7` is the schema style to copy: `"$schema": "https://json-schema.org/draft/2020-12/schema"`, `"$id": "https://github.com/ChristianPrzybulinski/agent-rules-kit/schemas/debt.schema.json"`, `title`, `type`, `required`, `additionalProperties: false`.
- kit `plugins/architect-sdd/skills/sdd-tasks/SKILL.md` (52 lines today; P1-08 extends it): `:30` `Each row contains `T-nn`, imperative title, exact files, proof, covered acceptance criteria, dependencies and state. ...`; `:33` `| ID | Task | Files | Proof | Covers | Depends on | State |`; `:52` `Done when: tasks are dependency ordered, independently provable, mapped both ways to criteria, pass the pre-cut checklist and are ready for one-at-a-time execution.`
- kit `plugins/architect-sdd/skills/sdd-implement/SKILL.md` (45 lines today; P1-08 rewrites §1 and §4): `:26` `1. Mark `doing` and read every named file.`; `:29` `4. Run the task's proof literally and summarize output in History.`; `:45` `Done when: all tasks and proofs are recorded, full gates pass, validation is READY, ...`.
- kit `plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md` (58 lines, limit 60): `:43` `Feature status moves forward: `proposed → clarified → planned → in-progress → validated → delivered` (or `cancelled`). `delivered` means merged to `main` with no flag or the flag on.`; `:49-56` the `docs/spec/` layout tree ending `└── debts/DEBT-nnn-slug.md`.
- kit `plugins/core/skills/session-handoff/SKILL.md:22` `- Run `git status --short` and the relevant base-to-HEAD log/diff in every touched repository.`; `:23` `- Read changed specs/status/history, literal verification outputs and user decisions.` (38 lines). kit `plugins/core/templates/doc-session-handoff.md:26` `- Working tree: clean | dirty: [`files`]` (34 lines).
- Project rows this feeds from: stratics-docs `docs/spec/features/FEAT-009.md:88` `| ID | Task | Files | Proof of completion | Covers | Depends on | Status | Complexity | Devin model | Wave |`; ids are `T0`, `T1`, ... (kit text says `T-nn`), so the schema accepts both forms.
- New files: `platforms/ci/schemas/progress.schema.json` (listed in `platforms/ci/schemas/INDEX.md` and `platforms/ci/README.md`); `platforms/kits/sdd/progress.example.json` (listed in `platforms/kits/sdd/INDEX.md`). No JSON goes under `plugins/*/templates/`: `check_kit.py:694-695` accepts only `^(spec|doc|project|kit)-[a-z0-9-]+\.md$` there.

## Change

1. kit `platforms/ci/schemas/progress.schema.json` (new file). Draft 2020-12, `$id` `https://github.com/ChristianPrzybulinski/agent-rules-kit/schemas/progress.schema.json`, title `Executor progress of FEAT-nnn`, `additionalProperties: false` at both levels:
   ```json
   {"required": ["feat", "generated", "tasks"],
    "properties": {
      "feat": {"type": "string", "pattern": "^FEAT-[0-9]{3,}$"},
      "generated": {"type": "string", "format": "date"},
      "updated": {"type": "string", "format": "date"},
      "tasks": {"type": "array", "minItems": 1, "items": {
        "type": "object", "additionalProperties": false,
        "required": ["id", "title", "files", "proof", "passes", "notes"],
        "properties": {
          "id": {"type": "string", "pattern": "^T-?[0-9]{1,3}$"},
          "title": {"type": "string", "minLength": 5, "maxLength": 200},
          "files": {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1}, "uniqueItems": true},
          "proof": {"type": "string", "minLength": 5},
          "passes": {"type": "boolean"},
          "notes": {"type": "string", "maxLength": 500},
          "issue": {"type": "integer", "minimum": 1}}}}}}
   ```
   `issue` is the task issue number from P1-08 (optional); `updated` is the date of the last `passes` change (optional).
2. kit `platforms/kits/sdd/progress.example.json` (new file): `feat` `FEAT-009`, `generated` `2026-10-06`, three tasks `T1`, `T2`, `T3` with real-looking titles, `files` as the Files cell split on `, `, `proof` as the Proof cell, `T2` with `passes: true` and `notes: "proof output in PR #21 How I tested"`, the others `passes: false` and `notes: ""`. At most 30 lines; it must validate (step 5 tests it).
3. kit `platforms/ci/validations/check_spec.py`. After the `targets` loop and before the FEAT<->REQ block (`:168`), add a `progress` pass:
   - load `schemas_dir / "progress.schema.json"` when `FULL` and present (outside the `for name in STRUCT` loop; keep `STRUCT` for frontmatter kinds only);
   - `pdir = spec_dir / "progress"`; when it is a directory, for every sorted `*.json`: `json.loads` (an invalid file fails with `<path>: invalid JSON: <error>`); with jsonschema, `js_validate(data, schema, format_checker=FormatChecker())` and fail as `<path>: schema progress: <message>`; without it, structural checks: required top-level keys, `feat` matches `^FEAT-\d{3,}$`, `tasks` is a non-empty list, each task has the six required keys and `isinstance(task["passes"], bool)`, each failure as `<path>: <reason>`;
   - in both modes: `path.stem != data["feat"]` fails `<path>: feat <id> != file name`; `data["feat"] not in feats` fails `<path>: feat <id> does not exist in features/`; a repeated task `id` fails `<path>: duplicate task id <id>`;
   - count the files and, when at least one was read, print `progress: OK (<n> files)` after the existing `spec: OK (...)` line. Keep the existing line byte-identical. Keep the module docstring (`:2-5`) accurate: add one sentence `Also validates docs/spec/progress/*.json (executor progress) when the folder exists.`
4. kit `platforms/tools/sync-project.sh:13`: `SCHEMAS="spec feature requirement decision debt progress"`. Nothing else changes; `kit_files` and `--check` follow the list. Keep it executable, shellcheck-clean, bash 3.2 syntax.
5. kit `platforms/ci/validations/test_check_spec.py`: add `class ProgressTest(unittest.TestCase)` reusing the `FEAT` fixture (copy the `setUp`/`feat`/`run_check` helpers or move them to a mixin; keep the 4 existing tests untouched). Helper `progress(name, data)` writes `progress/<name>.json` with `json.dumps`. Cases, each asserting the return code and, where the message is the same in both modes, the message: valid file with one FEAT -> 0 and `progress: OK (1 files)` in stdout; `feat` without FEAT file -> 1, `does not exist in features/`; file named `FEAT-002.json` with `feat: FEAT-001` -> 1, `!= file name`; `passes: "yes"` -> 1 (return code only); duplicate task id -> 1, `duplicate task id`; invalid JSON text -> 1, `invalid JSON`; `test_kit_example_validates`: copy `platforms/kits/sdd/progress.example.json` (path `VALIDATIONS.parent.parent / "kits/sdd/progress.example.json"`) into `progress/FEAT-009.json` next to a `FEAT-009` fixture -> 0.
6. kit `plugins/architect-sdd/skills/sdd-tasks/SKILL.md`: add one section, at most 7 lines, before the `Done when:` line:
   ```markdown
   ## 6. Write the progress file

   Create `docs/spec/progress/FEAT-nnn.json` from the table: one entry per row with `id`, `title`, `files` (the Files cell as a list), `proof` (the Proof cell), `passes: false`, `notes: ""`; `generated` is today. Schema: `platforms/ci/schemas/progress.schema.json`; example: `platforms/kits/sdd/progress.example.json`. Validate with `check.sh --spec docs/spec` (kit) or `.github/spec-lint/check_spec.py docs/spec .github/spec-lint/schemas` (project). Commit it with the task table.
   ```
   Extend `Done when:` with `and the progress file validates`. Stay at 80 lines or fewer after P1-08.
7. kit `plugins/architect-sdd/skills/sdd-implement/SKILL.md`: at the top of the execution section (the one that contains `read every named file`) add a step `Orient: read `docs/spec/progress/FEAT-nnn.json` and `git log --oneline -20`; pick the first task with `passes: false` whose dependencies pass; never trust a Markdown status cell over the file.` After the sentence `Run the task's proof literally` add: `Set `passes: true` in the progress file only after the proof's literal output is recorded; on failure keep `false` and put the first failing line in `notes`. Commit the file in the task's commit (checkpoint).` Extend `Done when:` with `every task in the progress file has passes: true`. At most 6 added lines; stay at 80 or fewer.
8. kit `plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md:43`: append to that line, same paragraph: `During implementation the executor's state is `docs/spec/progress/FEAT-nnn.json` (`passes` per task, set only after the literal proof output); after merge the task row and FEAT status derived from GitHub are the source of truth and the progress file is advisory.` In the layout tree insert `├── progress/FEAT-nnn.json` before the `└── debts/` line only if the file stays at 60 lines or fewer after P1-08; otherwise skip the tree line.
9. kit `plugins/core/skills/session-handoff/SKILL.md`: after the line starting `- Read changed specs/status/history` add `- For a FEAT in implementation, read `docs/spec/progress/FEAT-nnn.json`; the record links it and names the tasks with `passes: false`.` kit `plugins/core/templates/doc-session-handoff.md`: after line 26 add `- Progress: [`docs/spec/progress/FEAT-nnn.json`: n of m tasks pass | n/a]`. Descriptions and `plugins/core/INDEX.md` unchanged.
10. Indexes and docs: `platforms/ci/schemas/INDEX.md` new row `| `progress.schema.json` | `docs/spec/progress/FEAT-nnn.json` (executor progress) |` after `:15`; `platforms/ci/README.md` new row after `:16` with file-name rule `FEAT-nnn.json` = `feat`, change `:18` `The five spec schemas (`spec`, `feature`, `requirement`, `decision`, `debt`)` to `The six spec schemas (..., `debt`, `progress`)`, and extend `:23` scope with `+ progress/*.json (schema, feat exists, name = feat, unique task ids)`; `platforms/ci/validations/INDEX.md:7` scope becomes `a project's `docs/spec/` (frontmatters and `progress/*.json`) against `../schemas/``; `platforms/kits/sdd/INDEX.md` new row `| `progress.example.json` | example of `docs/spec/progress/FEAT-nnn.json` written by `sdd-tasks` and updated by `sdd-implement`; schema `platforms/ci/schemas/progress.schema.json` |`.
11. kit `CHANGELOG.md` under `## [Unreleased]`, `### Added`: one bullet naming the schema, the example, the `check_spec.py` pass, the `sync-project.sh` list, the four skill/reference edits, the why (assessment §5 harness row, §7 N6, the 128/3 measurement) and the proof (the acceptance commands with literal output).

## Out of scope

- Deriving task `Status` and FEAT `status` from GitHub, `spec_trace.py sync-status`, DPRO-014: P2-08. This prompt only states the precedence in `sdd-process.md` (step 8).
- Re-running `sync-project.sh` in stratics-docs so `.github/spec-lint/schemas/progress.schema.json` appears there, and the resulting `--check` divergence until then: P2-15.
- Issue per task, ten-column rows, worktree and PR per issue text in `sdd-tasks`/`sdd-implement`: P1-08. Verification gates (`/goal`, Stop hook) in `sdd-implement`: P3-07. Spec regimes: P3-04.
- Where the progress file lives when `docs/spec` is in another repository than the code (Stratics): a project rule, recorded by P2-15 or a DPRO, not by the kit.
- `init-spec.sh`, `VERSION`, skill descriptions, `plugins/architect-sdd/INDEX.md` (no description changes), `agents/openai.yaml` files.

## Acceptance criteria

- [ ] `python3 -c "import json; json.load(open('platforms/ci/schemas/progress.schema.json')); json.load(open('platforms/kits/sdd/progress.example.json')); print('json ok')"` prints `json ok`.
- [ ] `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` ends with `OK` and reports at least 11 tests (4 existing + 7 new); run it once with `pip install pyyaml jsonschema` available and once with `python3 -I -S` or in a venv without them, both `OK`.
- [ ] `grep -c 'SCHEMAS="spec feature requirement decision debt progress"' platforms/tools/sync-project.sh` prints `1`; `shellcheck platforms/tools/sync-project.sh` exits 0; `bash -n platforms/tools/sync-project.sh` exits 0; `test -x platforms/tools/sync-project.sh`.
- [ ] `tmp=$(mktemp -d) && platforms/tools/sync-project.sh "$tmp" && ls "$tmp/.github/spec-lint/schemas" | grep -c '\.schema\.json'` prints `6`; `platforms/tools/sync-project.sh --check "$tmp"` prints `sync: ... consistent with kit 10.1.0`.
- [ ] `grep -c 'progress.schema.json' platforms/ci/schemas/INDEX.md platforms/ci/README.md` prints `1` for each; `grep -c 'six spec schemas' platforms/ci/README.md` prints `1`; `grep -c 'progress.example.json' platforms/kits/sdd/INDEX.md` prints `1`; `grep -c 'progress/' platforms/ci/validations/INDEX.md` prints `1`.
- [ ] `grep -c 'docs/spec/progress/FEAT-nnn.json' plugins/architect-sdd/skills/sdd-tasks/SKILL.md plugins/architect-sdd/skills/sdd-implement/SKILL.md plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md plugins/core/skills/session-handoff/SKILL.md plugins/core/templates/doc-session-handoff.md` prints at least `1` for each; `grep -c 'git log --oneline -20' plugins/architect-sdd/skills/sdd-implement/SKILL.md` prints `1`; `grep -c 'source of truth' plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md` prints `1`.
- [ ] `wc -l plugins/architect-sdd/skills/sdd-tasks/SKILL.md plugins/architect-sdd/skills/sdd-implement/SKILL.md plugins/core/skills/session-handoff/SKILL.md` each <= 80; `wc -l plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md` <= 60; `wc -l platforms/kits/sdd/progress.example.json` <= 30.
- [ ] `platforms/tools/check.sh` ends with its `check: OK (...)` line; `platforms/tools/smoke.sh` exits 0; `python3 platforms/ci/validations/check_kit.py --links` exits 0.
- [ ] `git diff --name-only main...HEAD` lists no `VERSION`, no file under `plugins/*/templates/*.json`, and no path outside `platforms/ci/`, `platforms/kits/sdd/`, `platforms/tools/sync-project.sh`, `plugins/architect-sdd/`, `plugins/core/` and `CHANGELOG.md`.
- [ ] `grep -c 'progress' CHANGELOG.md` is at least `1` inside the `## [Unreleased]` block (`sed -n '/^## \[Unreleased\]/,/^## \[10.1.0\]/p' CHANGELOG.md | grep -c progress.schema.json` prints `1`).

## Conventions

- Everything committed is in English; plain ASCII punctuation in new text.
- No layout or path change: the 10.x layout is frozen; `plugins/`, `platforms/`, `docs/` and install destinations keep their paths; the schema goes under `platforms/ci/schemas/`, the example under `platforms/kits/sdd/`, never under `plugins/*/templates/` (names there must match `^(spec|doc|project|kit)-[a-z0-9-]+\.md$`).
- `VERSION` untouched; `CHANGELOG.md` gets a `## [Unreleased]` entry with what, why and proof.
- `INDEX.md` or `README.md` of every touched folder lists every entry by name (a folder never has both): `platforms/ci/schemas/INDEX.md`, `platforms/ci/README.md`, `platforms/ci/validations/INDEX.md`, `platforms/kits/sdd/INDEX.md`.
- Skill descriptions unchanged (40-160 chars each, total budget 7,200, measured 6,805 today with `grep -h '^description:' plugins/*/skills/*/SKILL.md | awk '{s+=length($0)-13} END {print s}'`); if you must change one, copy it verbatim into the plugin `INDEX.md` table.
- `SKILL.md` <= 80 lines; references <= 60 lines with frontmatter (`sdd-process.md` is `kind: detail`: no `verified`/`sources` needed).
- User-only skills stay user-only: `sdd-tasks`, `sdd-implement` and `session-handoff` keep `triggers: [user]`, `disable-model-invocation: true`, `agents/openai.yaml` with `policy.allow_implicit_invocation: false`; `allowed-tools` lowercase and unchanged.
- Every `platforms/**/*.sh` is executable, passes shellcheck and parses under bash 3.2 (no associative arrays, no `mapfile`).
- Conventional Commits with `Refs: P3-10`; PR body = What / Why / How I tested (literal output of the acceptance commands) / Refs (assessment §5 harness row, §7 N6).
- Gates: `platforms/tools/check.sh`; `platforms/tools/smoke.sh`; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`; `python3 platforms/ci/validations/check_kit.py --links`.
- Nothing here is Claude-specific; the executor may be Devin or Claude Code.

## Report back

Final message in three blocks: **done** (every created or edited path; each acceptance command with its literal result; the `check: OK (...)` line; the unittest `Ran N tests ... OK` line in both dependency modes), **unverified** (anything not run, for example `smoke.sh` steps that need an installed agent CLI, or the jsonschema-less run if no clean interpreter was available, each with the reason), **next step** (P2-15 to resync stratics-docs `.github/spec-lint/` so the new schema lands there; P2-08 for the derived status this file defers to). Proposed CHANGELOG line: `- `docs/spec/progress/FEAT-nnn.json`: executor progress file with `passes` per task, written by `sdd-tasks`, updated by `sdd-implement` after the literal proof and read at session start with `git log --oneline -20`; schema `platforms/ci/schemas/progress.schema.json`, example `platforms/kits/sdd/progress.example.json`, validated by `check_spec.py` (+7 tests) and copied by `sync-project.sh`; after merge the derived status is the source of truth (assessment §5 harness row, §7 N6).`
