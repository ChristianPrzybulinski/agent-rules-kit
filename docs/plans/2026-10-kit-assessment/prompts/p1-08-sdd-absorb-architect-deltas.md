# P1-08 — SDD absorbs the ARCHITECT.md deltas (issue per task, waves, model directive, task template)

Phase: 1 · Repos: kit · Branch to create: feat/p1-08-sdd-absorb-architect-deltas from main · Depends on: none · Effort: ~6 h

## Goal

Make the kit's SDD steps 6, 7 and 9 describe the flow the Stratics project actually runs, so that no project needs a private "deltas over the kit" file: one GitHub issue per task row (title `[FEAT-NNN Tn] <first ~8 words>`), task rows extended with `Complexity | Model | Wave`, waves that share only disjoint file sets, a generic model tier per complexity, an issue body that is the task template filled verbatim, one worktree and one PR per issue, cross-repo `Closes <owner>/<docs-repo>#N`, and architect review of every PR against FEAT/REQ/DEC. Measurable result: stratics-docs `docs/spec/ARCHITECT.md` deltas 1 to 5 and its "Issue body" section (lines 26-73 and 88-108 today) become redundant with kit text, the kit ships `platforms/kits/github/ISSUE_TEMPLATE/task.md` equal in fields to stratics-docs `.github/ISSUE_TEMPLATE/task.md`, and every kit gate stays green.

## Why

- assessment §4.6: `sdd-implement` prescribes a `feature/FEAT-nnn` branch, one squash PR per FEAT and a hand-typed `in-progress -> validated -> delivered` status, while the project works issue per task, in worktrees, with a PR per task merged by the review loop; `ARCHITECT.md` carries 8 deltas to correct a flow the kit describes but the project does not use.
- assessment §4.8: waves, the model directive by complexity, the executor prompt and the cut checklist live only in the project (`ops/review-loop`, `ARCHITECT.md`, `CONTRIBUTING.md`), so the kit cannot speed up a second repository or a second collaborator.
- assessment §6 item E2 asks exactly this: `sdd-tasks` and `sdd-to-card` absorb deltas 1 to 5, `task.md` becomes the canonical issue format, and `sdd-implement` describes worktree per issue, PR per task and `Closes <owner>/<docs-repo>#N`.
- Evidence the deltas earn their place: stratics-docs `docs/spec/ARCHITECT.md:63-64` records that 7 of 16 issues of one batch had review findings caused by the spec; `:61-62` records 6 rounds caused by three cut gaps (generated and build files such as `pom.xml`/`application.yml`/`.import` and tests, unnamed value domains, refused words in proofs). The kit's pre-cut checklist (`sdd-tasks` §5, in Unreleased) covers only four of these items.
- The kit's own task row and the project's disagree today: kit `plugins/architect-sdd/templates/spec-feature.md:60` has seven columns; stratics-docs `docs/spec/features/FEAT-009.md:88` has ten (`... | Status | Complexity | Devin model | Wave |`). The three extra columns are what `sdd-to-card` needs to fill `Directive`.

## Current state

- kit `plugins/architect-sdd/skills/sdd-tasks/SKILL.md:3`:
  `description: SDD step 6 — dependency-ordered implementation tasks. Use when a FEAT has an approved technical plan. Not for execution (skill sdd-implement).`
- kit `plugins/architect-sdd/skills/sdd-tasks/SKILL.md:30`:
  `Each row contains `T-nn`, imperative title, exact files, proof, covered acceptance criteria, dependencies and state. Mark dependency-independent rows `[P]`.`
- kit `plugins/architect-sdd/skills/sdd-tasks/SKILL.md:33`:
  `| ID | Task | Files | Proof | Covers | Depends on | State |`
- kit `plugins/architect-sdd/skills/sdd-tasks/SKILL.md:44-50`: `## 5. Pre-cut checklist (before issues are created)` with four bullets (Tests in scope, Cross-feature fields, Executable proof, Neighbour files). The file has 52 lines and no `references/` folder.
- kit `plugins/architect-sdd/templates/spec-feature.md:60`:
  `| ID | Task | Files | Proof of completion | Covers | Depends on | State |`
- kit `plugins/architect-sdd/skills/sdd-to-card/SKILL.md:3`:
  `description: SDD step 9 — sync a FEAT to GitHub Issues/Projects. Use when opening, updating or closing its card. Not for PR operations (skill github-cli).`
- kit `plugins/architect-sdd/skills/sdd-to-card/SKILL.md:20-21`:
  `- Issue title: `FEAT-nnn: <title>`.`
  `- Body: link the FEAT and requirements; summarize problem/scope/criteria instead of copying the specification.`
- kit `plugins/architect-sdd/skills/sdd-to-card/SKILL.md:33`:
  `For `status: delivered`, close the issue with the delivered PR reference. Do not create separate cards for REQ/DEC/DEBT unless the user explicitly requests a debt issue.`
- kit `plugins/architect-sdd/skills/sdd-implement/SKILL.md:22`:
  `Create or use `feature/FEAT-nnn-slug` from updated `main`; set `status: in-progress`. Work one task at a time unless independent `[P]` tasks have disjoint files.`
- kit `plugins/architect-sdd/skills/sdd-implement/SKILL.md:31`:
  `6. Commit atomically as `feat(scope): <task>` with `Refs: FEAT-nnn`; mark `done`.`
- kit `plugins/architect-sdd/skills/sdd-implement/SKILL.md:43`:
  `After READY and green gates, open a squash PR with criteria/proofs and `Refs: FEAT-nnn`. Set `validated` after the green PR and `delivered` after merge.`
- kit `plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md:24`:
  `Repeat `implement → validate` until READY. Run `to-card` after specify to open and after delivery to close.`
- kit `plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md:35` and `:37`:
  `| 7 | `sdd-implement` | Tasks | code/tests/docs; in-progress |`
  `| 9 | `sdd-to-card` | FEAT | synchronized GitHub issue |`
- kit `plugins/architect-sdd/INDEX.md:15` (the `sdd-to-card` row, description copied verbatim from the SKILL).
- kit `platforms/kits/github/README.md:7-14`: the "How to use" table lists `workflows/*.yml`, `PULL_REQUEST_TEMPLATE.md`, `CODEOWNERS`, `dependabot.yml`, `labels.json`, `scripts/labels-sync.sh`. No issue template exists under `platforms/kits/github/` (`ls platforms/kits/github` shows no `ISSUE_TEMPLATE`).
- kit `platforms/kits/github/ISSUE_TEMPLATE/task.md` (new file); must be listed in `platforms/kits/github/README.md` (the folder has a README, so no INDEX.md; a subfolder four levels deep under `platforms/kits/` needs no index of its own, `check_kit.py:729-730`).
- kit `plugins/architect-sdd/skills/sdd-tasks/references/waves-and-models.md`, `plugins/architect-sdd/skills/sdd-to-card/references/task-issue.md`, `plugins/architect-sdd/skills/sdd-implement/references/task-pr.md` (new files, `kind: detail`); `check_kit.py:624-637` requires each to have frontmatter, at most 60 lines and its file name mentioned in the owning SKILL.md.
- kit `CHANGELOG.md:11-17`: `### Changed` under `## [Unreleased]` already holds the `sdd-tasks` pre-cut checklist entry; add to it, do not restate it.
- Source of truth to de-project (read, never edit): stratics-docs `docs/spec/ARCHITECT.md:26-73` (deltas 1 to 5; the three new §5 bullets of step 1 come from `:55-60`; `:65-73` (wiring, success replies, pack manifest) are project-specific and stay out) plus the last sentence of delta 7 (`:80`, human executor: the model is a hint, `Complexity` sets the review depth) and `:88-108` (the "Issue body" section: `:96-102` the kit section to template field map, `:104-105` the rule that `Spec` and `DoD` are derived mechanically, which step 4 relies on); `.github/ISSUE_TEMPLATE/task.md:1-47`; `CONTRIBUTING.md:118-160` (§5 executor prompt: `:129-135` rules, `:138-145` self-check, `:147-149` PR body; `:159` the `[BLOCKER]` comment); `docs/collab/README.md:47-51` and `:63-80` (single backlog, cross-repo `Closes`, cut in wave order, filled verbatim).

## Change

1. kit `plugins/architect-sdd/skills/sdd-tasks/SKILL.md`. Replace line 30 with the first line below and lines 33-35 (inside the existing ```markdown fence, which stays) with the three table lines below, so the row carries ten columns and the wave rule is stated once:
   ```markdown
   Each row contains `T-nn`, imperative title, exact rooted files (tests included), proof, covered criteria, dependencies, state, and the three cut fields `Complexity` (Low|Med|High), `Model` (tier, see `references/waves-and-models.md`) and `Wave`. Mark dependency-independent rows `[P]`.

   | ID | Task | Files | Proof of completion | Covers | Depends on | State | Complexity | Model | Wave |
   |---|---|---|---|---|---|---|---|---|---|
   | T-01 | Define MoveRequest contract | protocol/... , tests/... | example validates | CA-1 | — | todo | Low | small | 0 |
   ```
   Add one line after "States:": `Waves: contracts, schemas and DECs go to wave 0, sequential; two tasks share a wave only when their file sets are disjoint and neither reads the other's output; wave numbers are FEAT-local and a cross-FEAT dependency points to a task cut earlier.` Extend §5 (do not duplicate the four existing bullets) with three bullets: generated and build files (`*.import`, `*.uid`, `*.translation`, `pom.xml`, `application.yml` or the project's equivalents) join `Files`; every contract field or table column names its value domain and the public identifier of any entity it names; a proof line contains none of the words the project's gates refuse (the issue's `Notes` field, filled by `sdd-to-card`, names the project's allowlist location; never hard-code it here). End §5 (after the seven bullets, before `Done when:`) with: `The architect reviews every PR of these tasks against FEAT/REQ/DEC; an executor's "done" report is not evidence, the diff and the re-run proofs are.` Keep the file at 80 lines or fewer; the detail goes to the reference below.
2. kit `plugins/architect-sdd/skills/sdd-tasks/references/waves-and-models.md` (new, at most 60 lines). Frontmatter: `description: Wave assignment, complexity tiers and the model directive for task rows. Load when filling the cut fields.` and `kind: detail`. Body: the wave rules of ARCHITECT.md delta 2 in kit terms; the tier mapping `Low -> small/fast tier`, `Med -> mid tier`, `High -> top tier at maximum effort` (the row value is `Med`, never `Medium`), with the sentence "a project maps tiers to vendor model names in its own AGENTS.md or ARCHITECT file; the kit never names a vendor model"; effort set once per tier in the executor's model picker; a human executor reads the tier as a hint and `Complexity` as review depth; a worked example of a three-task FEAT with wave 0 (contract), wave 1 (two disjoint tasks), wave 2 (integration).
3. kit `plugins/architect-sdd/templates/spec-feature.md:60-61`. Replace the header and separator with the ten-column header from step 1 (`| ID | Task | Files | Proof of completion | Covers | Depends on | State | Complexity | Model | Wave |` and `|---|---|---|---|---|---|---|---|---|---|`).
4. kit `plugins/architect-sdd/skills/sdd-to-card/SKILL.md`. New description (147 chars, copy it verbatim into `plugins/architect-sdd/INDEX.md:15`):
   ```yaml
   description: SDD step 9 — one GitHub issue per task row plus the FEAT card. Use when cutting issues or closing a FEAT. Not for PR operations (skill github-cli).
   ```
   Rewrite §1 as "Cut one issue per task row": title `[FEAT-nnn Tn] <first ~8 words of the Task cell>`; body = the project's `.github/ISSUE_TEMPLATE/task.md` (kit source `platforms/kits/github/ISSUE_TEMPLATE/task.md`) filled verbatim from the row, no rewriting, no added scope; `Spec` is the FEAT path derived from the title and `DoD` is the proof plus the gate commands of `<Repository>/AGENTS.md` § Commands, both filled mechanically; issues are cut in wave order, in the single backlog repository the project names, with the target repo in `Repository`; a FEAT card (`FEAT-nnn: <title>`) is optional and mirrors status as today. The FEAT frontmatter `card` holds only the optional FEAT card number; task issue numbers are not written to the FEAT (P2-08 derives state from GitHub), so §1's `card` bullet and §2's `card: null` rule refer to the FEAT card alone. Keep §2 to §4 but make §3 say that a task issue closes through its PR (`Closes <owner>/<docs-repo>#N`, cross-repo when the code lives elsewhere) and the FEAT card closes when every task issue is closed. Link `references/task-issue.md`. Stay at 80 lines or fewer.
5. kit `plugins/architect-sdd/skills/sdd-to-card/references/task-issue.md` (new, at most 60 lines, `kind: detail`, description: `Task issue contract — title, template fields, mechanical fields and cross-repo close line. Load when cutting or reviewing issues.`; no `: ` inside the value, pyyaml rejects an unquoted scalar that contains one). Body: the kit-section to template-field map de-projected from ARCHITECT.md `:96-102` (Context and Goal -> `Task` + `Spec`; Technical spec -> `Files`; Parallelism -> `Directive` wave + `Files` + `Depends on`; Directive -> `Directive` model; DoD -> `Proof of completion` + `DoD`); the rule that REQ/DEC ids are read from the FEAT's Relations and never copied; `Depends on` written as `FEAT-nnn Tn` or `#N`; freshly cut issues carry `status:proposed` until the architect approves the cut, then `status:planned` (the task-issue states reuse the FEAT labels with their FEAT meaning in `labels.json` left as is; `labels.json` is not edited here, and a project that wants distinct task-level labels adds them in its own labels file); an implementation session picks only `status:planned` issues whose `Depends on` chain is merged.
6. kit `platforms/kits/github/ISSUE_TEMPLATE/task.md` (new). The Stratics template with project names removed:
   ```markdown
   ---
   name: Task
   about: One row of a FEAT task table, ready for implementation
   title: "[FEAT-NNN Tn] "
   labels: ""
   assignees: ""
   ---

   ## Task
   <!-- one line: what gets built/changed, copied from the task row -->
   ## Spec
   <!-- docs/spec/features/FEAT-NNN.md, the FEAT in the title; its Relations list the REQ/DEC ids (never copied here) -->
   ## Repository
   <!-- the target repository name -->
   ## Files
   <!-- exact rooted paths from the task row, tests and generated files included -->
   ## Proof of completion
   <!-- the verifiable commands from the task row, one per line -->
   ## DoD
   <!-- Proof of completion above + the gate commands in <Repository>/AGENTS.md section Commands -->
   ## Covers
   <!-- CA ids -->
   ## Depends on
   <!-- FEAT-NNN Tn / issue #N / none -->
   ## Directive
   Model: <!-- small | mid | top --> | Complexity: <!-- Low | Med | High --> | Wave: <!-- n -->
   ## Notes
   <!-- constraints, do-not list, proof allowlist location -->
   ```
   Keep a blank line between each heading and its comment when writing the file (compressed here for length).
7. kit `platforms/kits/github/README.md`. Insert the row `| `ISSUE_TEMPLATE/task.md` | `.github/ISSUE_TEMPLATE/task.md` (one issue per task row, filled verbatim by `sdd-to-card`) |` directly after the `PULL_REQUEST_TEMPLATE.md` row and append the bullet "`ISSUE_TEMPLATE/task.md` is the body contract `sdd-to-card` fills; the `Directive` tiers map to vendor models in the project, never in the kit." at the end of `## Notes`; P1-05 and P1-06 edit line 19 of the same Notes list, so rebase if they merged first and keep their sentences.
8. kit `plugins/architect-sdd/skills/sdd-implement/SKILL.md`. Replace §1 with "Start one worktree per issue": `git worktree add ../<repo>-<N> -b feature/FEAT-nnn-Tn-<slug> main` (worktree commands: skill `parallelize`, its reference worktrees.md — do not put `references/worktrees.md` in backticks, the checker resolves that against sdd-implement/), read the issue body as the spec and only the artifacts its `Spec` line names, change only the paths in `Files` (plus a `changelog.d/` fragment when the repo uses one). Replace the step that reads `6. Commit atomically as `feat(scope): <task>` with `Refs: FEAT-nnn`; mark `done`.` (line 31 on main, before your §1 edit) with `6. Commit atomically with Conventional Commits and `Refs: FEAT-nnn Tn`; `git status --porcelain` is empty before the PR; mark `done` when the PR merges.` Replace §4 with "Open one PR per issue": after the task's proofs and the DoD commands from `<repo>/AGENTS.md` § Commands pass, open a PR whose body has What, Why, How I tested (literal output), Proof (one allowlisted command per line) and the last line `Closes <owner>/<docs-repo>#N`; never push to `main`, force-push, rebase or merge; the architect reviews the diff against FEAT/REQ/DEC and merges. Keep the §3 paragraphs that start `Use the `living-docs` reference` and `Incomplete work may merge only behind a recorded flag` unchanged (lines 37-39 on main); do the §1 edit last or anchor on text, never on post-edit line numbers. Link `references/task-pr.md`. Stay at 80 lines or fewer.
9. kit `plugins/architect-sdd/skills/sdd-implement/references/task-pr.md` (new, at most 60 lines, `kind: detail`, description: `Executor contract for one task issue — scope, proof lines, self-check, PR body and stop conditions. Load before implementing an issue.`; no `: ` inside the value). Body: the generic form of stratics-docs `CONTRIBUTING.md:129-152`: scope = `Files` cell; DoD commands from AGENTS.md; proof lines start with a command from the project's allowlist and contain no `$(...)`, backticks or redirection other than to `/dev/null`, and none of the words the gates refuse; fixture secrets are low-entropy placeholders; the four-step self-check (`git diff --name-only origin/main...HEAD` inside `Files`; one line per binding decision; every proof exits 0 at HEAD; a path needed outside `Files` stops the work and names the path); write the PR body outside the worktree; on ambiguity or a contradicted decision stop without guessing and record `[BLOCKER] <one line>` on the issue.
10. kit `plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md`. Replace line 24 with: `Repeat `implement → validate` per issue until READY. Run `to-card` after `tasks` to cut one issue per task row (wave order) and after delivery to close; `implement` runs in one worktree per issue and opens one PR per issue, which the architect reviews before merge.` Leave the flow diagram (lines 17-22, `to-card` as the last step with output `issue`) unchanged; it shows the closing run. Change table rows 7 and 9 to `| 7 | `sdd-implement` | one task issue | code/tests/docs; PR per issue |` and `| 9 | `sdd-to-card` | task rows + FEAT | one issue per task, FEAT card |`. Keep the file at 60 lines or fewer (58 today).
11. kit `CHANGELOG.md`, under `## [Unreleased]`: an `### Added` bullet for `platforms/kits/github/ISSUE_TEMPLATE/task.md` and the three references, and a `### Changed` bullet for `sdd-tasks`/`sdd-to-card`/`sdd-implement`/`sdd-process.md`/`spec-feature.md`, each with what, why (assessment §4.6, §6 E2) and proof (the commands of the acceptance criteria with their literal result).

## Out of scope

- Deriving task `State` and FEAT status from merged PRs, and removing hand-typed status: P2-08. This task keeps the status words of `sdd-process.md:43`.
- The orchestrator loop, verdict JSON, proof allowlist file and round policy as kit content (`process-loop` plugin): P3-08. Here the allowlist is only referenced as "the project's allowlist".
- Verification gates inside `sdd-implement` and worktree cleanup in `reviewer`: P3-07. P3-07 inserts a step after `Run the task's proof literally` in §2; keep that sentence verbatim.
- Merging `sdd-analyze` and `sdd-audit`: P3-06. Spec regimes and FEAT template changes beyond the task table header: P3-04.
- Editing stratics-docs (`ARCHITECT.md`, `CONTRIBUTING.md`, `task.md`): read-only sources here; their simplification is a follow-up stratics-docs prompt (not yet written in this plan) that deletes ARCHITECT.md deltas 1 to 5 and the Issue body section, and points `CONTRIBUTING.md` §5 and `docs/collab/README.md` § Issue cutting at the kit text. Do not use the number P2-15 for it: `p2-15-apply-sync-to-stratics-repos.md` regenerates the Stratics agent configuration and explicitly leaves the ARCHITECT.md deltas to a separate PR.
- `plugins/infra-github/skills/branching-and-versioning/SKILL.md:18` (`feature/FEAT-nnn-name`) stays; the per-task branch name in step 8 is a refinement of it, not a replacement.
- `platforms/kits/github/labels.json`: no new labels (`wave-n`, `model:*` stay project labels).

## Acceptance criteria

- [ ] `platforms/tools/check.sh` -> exit 0 and its output contains one line starting with `check: OK (`; a trailing `check: claude plugin validate skipped (claude not in PATH)` line is expected without the Claude CLI and goes to the unverified block. If `check.sh` is already red on `main` for paths outside this task (docs/plans links), report the identical failure list before and after your change in the unverified block and do not fix those files here.
- [ ] `platforms/tools/smoke.sh` -> exit 0.
- [ ] `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` -> `OK`.
- [ ] `python3 platforms/ci/validations/check_kit.py --links` -> exit 0, or, when it is already red on `main` for paths under `docs/plans/**` only (it is today: every FAIL line names `docs/plans/2026-10-kit-assessment/`), the identical FAIL list before and after your change with no line under `plugins/` or `platforms/` (report it in the unverified block, as for `check.sh`).
- [ ] `wc -l plugins/architect-sdd/skills/sdd-tasks/SKILL.md plugins/architect-sdd/skills/sdd-to-card/SKILL.md plugins/architect-sdd/skills/sdd-implement/SKILL.md` -> each <= 80; `wc -l plugins/architect-sdd/skills/*/references/*.md` -> each <= 60.
- [ ] `grep -c "kind: detail" plugins/architect-sdd/skills/sdd-tasks/references/waves-and-models.md plugins/architect-sdd/skills/sdd-to-card/references/task-issue.md plugins/architect-sdd/skills/sdd-implement/references/task-pr.md` -> 1 each.
- [ ] `grep -c "| State | Complexity | Model | Wave |" plugins/architect-sdd/skills/sdd-tasks/SKILL.md plugins/architect-sdd/templates/spec-feature.md` -> 1 each.
- [ ] `grep -c "\[FEAT-nnn Tn\]" plugins/architect-sdd/skills/sdd-to-card/SKILL.md` -> >= 1; `grep -c "Closes <owner>/<docs-repo>#N" plugins/architect-sdd/skills/sdd-implement/SKILL.md plugins/architect-sdd/skills/sdd-to-card/SKILL.md` -> >= 1 each.
- [ ] `grep -c "git worktree add" plugins/architect-sdd/skills/sdd-implement/SKILL.md` -> 1; `grep -c "git status --porcelain" plugins/architect-sdd/skills/sdd-implement/SKILL.md` -> 1; `grep -c "feature/FEAT-nnn-slug" plugins/architect-sdd/skills/sdd-implement/SKILL.md` -> 0.
- [ ] `grep -rn -i "opus\|sonnet\|swe\b\|stratics\|ChristianPrzybulinski" plugins/architect-sdd/skills plugins/architect-sdd/templates plugins/architect-sdd/INDEX.md platforms/kits/github/ISSUE_TEMPLATE` -> no output (tiers and owners stay generic; `agents/researcher.md` and the plugin manifests are not in scope).
- [ ] `grep -c "^## " platforms/kits/github/ISSUE_TEMPLATE/task.md` -> 10, and `diff <(grep "^## " platforms/kits/github/ISSUE_TEMPLATE/task.md) <(grep "^## " <stratics-docs>/.github/ISSUE_TEMPLATE/task.md)` -> empty (same ten fields in the same order; run against a local clone of stratics-docs). Without a clone, compare against this literal list, in order: Task, Spec, Repository, Files, Proof of completion, DoD, Covers, Depends on, Directive, Notes.
- [ ] `grep -c "value domain" plugins/architect-sdd/skills/sdd-tasks/SKILL.md` -> 1; `grep -c "is not evidence" plugins/architect-sdd/skills/sdd-tasks/SKILL.md` -> 1; `grep -c "mid tier" plugins/architect-sdd/skills/sdd-tasks/references/waves-and-models.md` -> >= 1; `grep -c "git diff --name-only origin/main...HEAD" plugins/architect-sdd/skills/sdd-implement/references/task-pr.md` -> 1.
- [ ] `grep -c "ISSUE_TEMPLATE" platforms/kits/github/README.md` -> >= 2.
- [ ] `grep -F "$(grep '^description:' plugins/architect-sdd/skills/sdd-to-card/SKILL.md | cut -d' ' -f2-)" plugins/architect-sdd/INDEX.md` -> 1 line (description verbatim in the plugin index).
- [ ] `grep -c "to-card\` after \`tasks\`" plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md` -> 1.
- [ ] `awk '/^## \[Unreleased\]/{f=1;next} /^## \[/{f=0} f' CHANGELOG.md | grep -c "ISSUE_TEMPLATE/task.md"` -> >= 1; `cat VERSION` -> `10.1.0`.

## Conventions

- Everything committed is in English. No layout or path change (10.x layout frozen; the new folder `platforms/kits/github/ISSUE_TEMPLATE/` is content inside an existing kit folder, not a new install destination). `VERSION` untouched.
- `CHANGELOG.md` gets `## [Unreleased]` entries with what, why and proof.
- `platforms/kits/github/README.md` lists the new entry; `plugins/architect-sdd/INDEX.md` carries the new `sdd-to-card` description verbatim. A folder never has both INDEX.md and README.md.
- Skill description 40 to 160 chars, form `<what>. Use when <trigger>. Not for <neighbor> (skill <x>).`; all descriptions together <= 7,200 chars (6,803 today, +6 with the new `sdd-to-card` text).
- SKILL.md <= 80 lines; references <= 60 lines with frontmatter (`kind: detail` needs `description` only; `kind: fact` would need `verified` + `sources`).
- Templates under `plugins/*/templates/` keep the `^(spec|doc|project|kit)-[a-z0-9-]+\.md$` name; the GitHub issue template under `platforms/kits/github/ISSUE_TEMPLATE/` is outside that rule and must keep the name GitHub reads (`task.md`).
- User-only skills stay user-only: `sdd-tasks`, `sdd-to-card` and `sdd-implement` keep `triggers: [user]`, `disable-model-invocation: true` and `agents/openai.yaml` with `policy.allow_implicit_invocation: false`; `allowed-tools` stay lowercase and unchanged.
- Backtick paths in SKILL.md, references, `platforms/**/*.md` and INDEX.md must resolve (`check_kit.py` fails on a broken backtick path); a reference escaping its plugin root fails too, so point to `parallelize` by skill name and reference file name, not by a `../../../core/...` path. A backtick path starting with `references/` is resolved against the current skill folder; name another skill's reference by bare file name only.
- The kit writes the placeholder as `FEAT-nnn` in SKILL/reference text and `[FEAT-NNN Tn]` only inside the GitHub template's `title:` field, mirroring the project template; do not harmonize them.
- Conventional Commits with `Refs: P1-08`; PR body = What / Why / How I tested (literal output) / Refs.
- Gates (kit touched): `platforms/tools/check.sh`; `platforms/tools/smoke.sh`; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`; `python3 platforms/ci/validations/check_kit.py --links`.

## Report back

Final message in three blocks: **done** (every created or edited path, each acceptance command with its literal result, the `check: OK (...)` line of `check.sh`), **unverified** (anything not run, for example `claude plugin validate` inside `check.sh` when `claude` is not in PATH, named with the reason), **next step** (a follow-up stratics-docs prompt, not yet written in this plan and not numbered P2-15, that deletes ARCHITECT.md deltas 1 to 5 and the Issue body section and points `CONTRIBUTING.md` §5 and `docs/collab/README.md` § Issue cutting at the kit text; P2-08 for derived status). Proposed CHANGELOG line: `- `sdd-tasks`/`sdd-to-card`/`sdd-implement`: one issue per task row (`[FEAT-nnn Tn]`), ten-column task rows with `Complexity | Model | Wave`, generic model tiers, worktree and PR per issue with cross-repo `Closes`, and the kit issue template `platforms/kits/github/ISSUE_TEMPLATE/task.md`; absorbs stratics-docs ARCHITECT.md deltas 1-5 (assessment §4.6, §6 E2).`
