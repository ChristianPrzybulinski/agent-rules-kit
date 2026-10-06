# P3-05 — sdd-spike: a prototype lane for game feel

Phase: 3 · Repos: kit · Branch to create: feat/p3-05-sdd-spike-lane from main · Depends on: none (touches `sdd-process.md` only in the entry-point sentence and never a step number; coordinate with P3-04 (entry-point rewrite of `sdd-process.md`) and P3-06 (step-table renumbering), which edit the same file) · Effort: ~3 h

## Goal

Add a user-only skill `sdd-spike` to `plugins/architect-sdd` that lets a session iterate game feel (movement, camera, battle feedback, UI) on a throwaway `spike/<topic>` branch, time-boxed to two days, with no coverage or lint gate and no spec edits, whose only deliverables are a GIF, video or screenshots, a filled `doc-spike-report.md`, and, when a product choice emerged, a proposed DGME or DTEC. The spike branch never merges to `main`: it is deleted after the report or re-implemented through `sdd-specify` and the rest of the pipeline. Measurable result: `platforms/tools/check.sh` exits 0 and its summary line reports exactly one more skill and one more template than the same command printed on `main` before your change (on main 2026-10-06, before P2-09/P3-06: 43→44 skills, 18→19 templates; after P3-06: 42→43 skills), with all descriptions at or under 7,200 chars; `sdd-process.md` names the lane as an entry point; `branching-and-versioning` §1 states the `spike/` policy; a reader of the three files can run a spike without touching `docs/spec/`.

## Why

- assessment §4.6: the Stratics spec has ~9.5k lines for ~3k lines of new code; measured today, stratics-docs `docs/spec/**/*.md` totals 9,451 lines, while stratics-client has 18 GDScript files outside `addons/` and none of them calls `move_and_slide`, `velocity` or `move_toward` (grep, 2026-10-06). The spec was written before a character moved on screen.
- assessment §6 item E3: "A game needs to iterate on "feel" (movement, camera, battle feedback) before specifying."; the prescribed shape is a `spike/<topic>` branch, a deadline of two days or less, no coverage gate, a video or GIF plus a proposed DGME as the only deliverable, and code that is discarded or re-implemented via SDD.
- The pipeline has no such lane: `plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md:12-13` offers only `/grilling` then `sdd-specify` for a vague idea, so a feel question enters the spec pipeline immediately.
- The branch policy forbids the lane by omission: `plugins/infra-github/skills/branching-and-versioning/SKILL.md:18` allows `feature/`, `fix/`, `docs/`, `chore/` only, and §4 requires every branch to end in a squash PR.
- The full gates would make a two-day spike impossible: `plugins/dev-core/skills/testing/SKILL.md:19` requires 100% line and branch coverage plus mutation score for battle logic, and `plugins/architect-sdd/skills/sdd-implement/SKILL.md:37` demands "full repository gates" before `validate-implementation`.
- Stratics already did one spike informally: stratics-docs `docs/spec/features/FEAT-006.md:89` records "the transport spike (kept, not thrown away)" as task T7, with no report, no time box and no rule on what happens to its code.

## Current state

- `plugins/architect-sdd/INDEX.md:3-15` (measured on main 2026-10-06 before P2-09/P3-06): the `skills/` table has one row per skill folder (nine today, `sdd-analyze` to `sdd-to-card`; eight after P3-06), each `| \`<name>\` | <description> |`; `:24-31` lists the six `spec-*.md` templates as `- \`spec-*.md\`` bullets. There is no `templates/INDEX.md` (the plugin INDEX is the folder's index; `check_kit.py:771-782` fails when an entry name is missing from it, and `:789-792` fails when a skill description differs from its frontmatter).
- `plugins/architect-sdd/skills/sdd-specify/SKILL.md:1-14` is the user-only pattern to copy: `triggers:` / `  - user`, `disable-model-invocation: true`, `allowed-tools:` with lowercase names, `argument-hint: "<feature description in natural language>"`. `plugins/architect-sdd/skills/sdd-specify/agents/openai.yaml:1-2`: `policy:` / `  allow_implicit_invocation: false`.
- `plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md:10-13`: `## Entry points` / `- Vague idea → \`/grilling\` first, then \`sdd-specify\` when problem/value is describable.` / `- Described feature → \`sdd-specify\`; new project/principles → \`sdd-constitution\`.` The file is 58 lines (limit 60, `check_kit.py:27`), `kind: detail`.
- `plugins/infra-github/skills/branching-and-versioning/SKILL.md:18`: `\`main\` is the only long-lived branch and stays green. Update it, then create \`feature/FEAT-nnn-name\` (\`fix/\`, \`docs/\`, \`chore/\` for non-features). Do not create develop or release branches.` (40 lines; description at `:3` stays unchanged, so `plugins/infra-github/INDEX.md:7` stays unchanged.)
- `plugins/architect-sdd/templates/spec-decision.md:1-16`: frontmatter `id`, `title`, `status: proposed`, `date`, `deciders`, `kind`, `features`, `supersedes`; `:16`: `kind` fixes the prefix (`game` → `DGME`, `tech` → `DTEC`). The spike's decision proposal uses this template unchanged.
- `plugins/core/hooks/hooks.json`: the guard blocks `rm -rf`, `git push --force`, `git reset --hard`, `git clean -f` and destructive SQL; it does not block `git branch -D` or `git push --delete`, so the skill must make branch deletion an explicit user action.
- Measured on main 2026-10-06 before P2-09/P3-06: 43 skills, descriptions total 6,805 chars (`check_kit.py:25` budget 7,200), headroom 395 chars for the new description; after P3-06 the kit has 42 skills and about 6,660 chars. Re-measure on your `main` before adding anything.
- (new file) `plugins/architect-sdd/skills/sdd-spike/SKILL.md`, listed in `plugins/architect-sdd/INDEX.md`.
- (new file) `plugins/architect-sdd/skills/sdd-spike/agents/openai.yaml`.
- (new file) `plugins/architect-sdd/templates/doc-spike-report.md`, listed in `plugins/architect-sdd/INDEX.md` under `templates/`.

## Change

1. kit: create `plugins/architect-sdd/skills/sdd-spike/SKILL.md` (at most 80 lines, target 55). Frontmatter verbatim:
   ```yaml
   ---
   name: sdd-spike
   description: Prototype lane for game feel. Use when movement, camera, battle feedback or UI must be felt on screen before a FEAT exists. Not for specs (skill sdd-specify).
   argument-hint: "[topic] [max-days]"
   triggers:
     - user
   disable-model-invocation: true
   allowed-tools:
     - read
     - grep
     - glob
     - exec
     - edit
   ---
   ```
   Body outline, as `##` sections in this order: `# SDD lane: Spike` title line; the first body line after the H1 points to `../sdd-constitution/references/sdd-process.md` and `../../templates/doc-spike-report.md` (both backtick paths are checked by `check_kit.py:831-832`, so spell them exactly). `## 1. Qualify`: the question must be about feel (movement, camera, battle feedback, UI) and unanswerable by reading the spec; if a FEAT already specifies it, stop and use `sdd-implement`. `## 2. Open the lane`: `git switch -c spike/<topic>` from updated `main`; `max-days` defaults to 2 and never exceeds 2; write the question and the end date as the first commit (`chore(spike): open spike/<topic>, question: ..., ends YYYY-MM-DD`). `## 3. Rules while spiking`: no file under `docs/spec/` changes; no coverage, lint, mutation or `validate-implementation` gate applies; any code shape is allowed; measure what the question asks (frame time, input-to-motion latency, tile crossing time, hit-feedback delay) and record the numbers. `## 4. Deliver`: a GIF, video or screenshot set attached to the PR or issue; a filled `doc-spike-report.md` posted in the issue or PR body (never under `docs/spec/`); when a product choice emerged, a proposed `DGME-nnn` or `DTEC-nnn` from `../../templates/spec-decision.md` with `status: proposed`, opened as a normal docs PR by the user. `## 5. Close the lane`: the spike branch never merges to `main`: after the report, ask the user to delete it (`git branch -D spike/<topic>`, `git push origin --delete spike/<topic>` are the user's commands) or to re-implement the kept idea through `sdd-specify`, then `sdd-plan`, `sdd-tasks` and `sdd-implement`; the report's keep list is the input to `sdd-specify`. End with `Done when: the question has a measured answer, the report and media are posted, any decision is a proposed DGME/DTEC, and the spike branch is deleted or scheduled for re-implementation.`
2. kit: create `plugins/architect-sdd/skills/sdd-spike/agents/openai.yaml` verbatim:
   ```yaml
   policy:
     allow_implicit_invocation: false
   ```
3. kit: create `plugins/architect-sdd/templates/doc-spike-report.md` (at most 40 lines, no frontmatter: `check_kit.py:678-685` and `:697-705` require frontmatter only for the six `spec-*` stems in `SPEC_MAP`; `doc-*` templates are checked for the name regex only, `:694-695`). Title `# Spike report - spike/<topic> - YYYY-MM-DD`. Header line: `Question:` one sentence; `Branch:`; `Opened/closed:` dates; `Time spent:` hours. Sections in order: `## What was built` (bullets, files or scenes, no code); `## What was learned` (facts marked `[FACT]`, guesses marked `[HYPOTHESIS]`); `## Measurements` (table `| Metric | Value | How measured |`, at least one row); `## Decision proposal` (`DGME-nnn`/`DTEC-nnn` id and one-sentence proposal, or `none`); `## Discard / keep` (table `| Item | Keep or discard | Where it goes |`, where "keep" means re-implemented via SDD, never merged as-is); `## Media` (links to GIF, video or screenshots); `## Unverified`.
4. kit: edit `plugins/architect-sdd/INDEX.md`. Insert this row in the `skills/` table after the `sdd-plan` row (alphabetical: `sdd-plan`, `sdd-specify`, `sdd-spike`, `sdd-tasks`), copied verbatim from the frontmatter:
   ```
   | `sdd-spike` | Prototype lane for game feel. Use when movement, camera, battle feedback or UI must be felt on screen before a FEAT exists. Not for specs (skill sdd-specify). |
   ```
   Add `- \`doc-spike-report.md\`` as the first bullet of the `templates/` list (alphabetical before `spec-debt.md`).
5. kit: edit `plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md`. Locate the vague-idea entry point by content, not line number. (a) If `grep -c "^## Entry points" plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md` prints 1 (P3-04 not merged): add the bullet below after the `- Vague idea → ...` bullet, provided the file stays at or under 60 lines:
   ```
   - Vague feel question (movement, camera, battle feedback, UI) → `sdd-spike`; its report feeds `sdd-specify`. Spike branches never merge.
   ```
   Otherwise append `; vague feel question (movement, camera, battle feedback, UI) → \`sdd-spike\`, whose report feeds \`sdd-specify\` and whose branch never merges` to that bullet. (b) If it prints 0 (P3-04 merged): append the same clause to the `Entry: ...` sentence in the `Repeat ... to close.` paragraph, adding no line. Never add a step row or number; P3-06 owns the table. Keep the file at or under 60 lines.
6. kit: edit `plugins/infra-github/skills/branching-and-versioning/SKILL.md:18` by appending one sentence to the paragraph:
   ```
   `spike/<topic>` is the only exception: it is time-boxed (skill sdd-spike), never merged to `main`, and deleted after its report.
   ```
   Then in §4 (`:32`) prefix the paragraph with `Except for \`spike/\` branches, ` and lowercase the following word (`rebase`) so the squash-PR rule does not contradict it. Description at `:3` unchanged.
7. kit: add to `CHANGELOG.md` under `## [Unreleased]` / `### Added` one bullet: what (`sdd-spike` skill, `doc-spike-report.md` template, `spike/` branch policy, SDD entry point), why (assessment §4.6, §6 E3: 9,451 spec lines before any movement code in stratics-client), proof (the `check.sh` summary line with the new skill and template counts).

## Out of scope

- Renumbering or merging `sdd-analyze` and `sdd-audit` in `sdd-process.md` (P3-06).
- The spec regimes (spec-anchored vs spec-first) that decide which spike outcomes become contracts (P3-04).
- Verification gates inside `sdd-implement` and worktree cleanup (P3-07); the spike lane waives gates, it does not redefine them.
- Hook-guard patterns for `git branch -D` or `git push --delete` (P1-07); this prompt only makes deletion a user action.
- Godot movement model, netcode or performance references the spike may measure against (P1-04, P3-01).
- Skill evals for the new skill (P3-09). Changes to stratics-docs, stratics-client, stratics-server: none in this prompt.

## Acceptance criteria

- [ ] `test -f plugins/architect-sdd/skills/sdd-spike/SKILL.md && wc -l < plugins/architect-sdd/skills/sdd-spike/SKILL.md` prints a number at or under 80.
- [ ] `grep -c "^disable-model-invocation: true$" plugins/architect-sdd/skills/sdd-spike/SKILL.md` prints `1`; `grep -c "^  - user$" plugins/architect-sdd/skills/sdd-spike/SKILL.md` prints `1`; `grep -c "^  - model$" plugins/architect-sdd/skills/sdd-spike/SKILL.md` prints `0`.
- [ ] `grep -c "allow_implicit_invocation: false" plugins/architect-sdd/skills/sdd-spike/agents/openai.yaml` prints `1`.
- [ ] `python3 -c "import re;s=open('plugins/architect-sdd/skills/sdd-spike/SKILL.md').read();d=re.search(r'^description: (.*)$',s,re.M).group(1);print(len(d), 'Use when' in d, 'Not for' in d)"` prints a number from 40 to 160, `True True`.
- [ ] `grep -c "docs/spec" plugins/architect-sdd/skills/sdd-spike/SKILL.md` prints at least `1` (the no-spec-edit rule) and `grep -ci "never merge" plugins/architect-sdd/skills/sdd-spike/SKILL.md` prints at least `1`.
- [ ] `grep -c '^| `sdd-spike` |' plugins/architect-sdd/INDEX.md` prints `1`; `grep -c "doc-spike-report.md" plugins/architect-sdd/INDEX.md` prints `1`; `grep -c "sdd-spike" plugins/architect-sdd/INDEX.md` prints `1`.
- [ ] `ls plugins/architect-sdd/templates/doc-spike-report.md` succeeds; `grep -c "^## " plugins/architect-sdd/templates/doc-spike-report.md` prints `7`; `wc -l < plugins/architect-sdd/templates/doc-spike-report.md` is at or under 40.
- [ ] `grep -c "sdd-spike" plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md` prints `1`; `wc -l < plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md` is at or under 60; `grep -c "^| .* \`sdd-spike\`" plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md` prints `0` (no step row).
- [ ] `grep -c "spike/" plugins/infra-github/skills/branching-and-versioning/SKILL.md` prints `2`; `git diff main -- plugins/infra-github/INDEX.md` is empty.
- [ ] `python3 -c "import re,glob;print(sum(len(re.search(r'^description:\s*(.*)$',open(p).read(),re.M).group(1).strip()) for p in glob.glob('plugins/*/skills/*/SKILL.md')))"` prints a number at or under 7200.
- [ ] `sed -n "/^## \[Unreleased\]/,/^## \[/p" CHANGELOG.md | grep -c "sdd-spike"` prints at least `1`; `git diff main -- VERSION` is empty.
- [ ] `LC_ALL=C.UTF-8 grep -rn --include=*.md -P "\x{2014}" plugins/architect-sdd/skills/sdd-spike plugins/architect-sdd/templates/doc-spike-report.md` prints nothing (or, without a UTF-8 locale, `grep -rn -- "—" <same paths>`), or only the title lines if you kept the repo's em-dash title style on purpose (state which in the PR).
- [ ] Gates: `platforms/tools/check.sh` exits 0 and its last line `check: OK (... skills, ... templates, ...)` shows one more skill and one more template than the same command on `main` (18→19 templates today; check.sh prints kit-wide totals only, never per-plugin counts); `ls plugins/architect-sdd/templates | wc -l` prints 7; `platforms/tools/smoke.sh` exits 0; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` passes; `python3 platforms/ci/validations/check_kit.py --links` exits 0.

## Conventions

- Everything committed is in English. No layout or path change: the skill lives in `plugins/architect-sdd/skills/`, the template in `plugins/architect-sdd/templates/`; nothing moves. `VERSION` untouched.
- `CHANGELOG.md` gets a `## [Unreleased]` entry with what, why and proof (step 7).
- `plugins/architect-sdd/INDEX.md` lists every entry by name; the folder has no README.md, so do not create one, and do not create `templates/INDEX.md`.
- Skill description 40 to 160 chars in the form `<what>. Use when <trigger>. Not for <neighbor> (skill <x>).`, copied verbatim into the INDEX table; all descriptions together at or under 7,200 chars (budget on main + 158 chars if the given description is used unchanged; 6,805 on main 2026-10-06 before P2-09/P3-06).
- SKILL.md at or under 80 lines; the edited reference `sdd-process.md` at or under 60 lines and keeps `kind: detail` (no `verified`/`sources` needed).
- Template name matches `^(spec|doc|project|kit)-[a-z0-9-]+\.md$` (`doc-spike-report.md` does).
- `allowed-tools` lowercase (`read`, `grep`, `glob`, `exec`, `edit`); no `agents/*.md` is created, so no Claude tool-name mirror is needed. User-only skill = `triggers: [user]` + `disable-model-invocation: true` + `agents/openai.yaml` with `policy.allow_implicit_invocation: false`; `check_kit.py:614-616` fails if any of the three is missing.
- No `platforms/**/*.sh` is touched; no hook change (the guard stays PreToolUse only, cases file untouched).
- Conventional Commits with `Refs: P3-05` (e.g. `feat(architect-sdd): add sdd-spike prototype lane and spike report template`). PR body = What / Why / How I tested (literal output of the four gates and the grep checks) / Refs.
- This change is not Claude-specific: Devin and Codex read the same `SKILL.md`; the Codex policy file is what makes it user-only there.

## Report back

Final message, in this order: `done`: every created or edited file by repo-relative path, and every command from Acceptance criteria with its literal output (the `check.sh` summary line verbatim, the description length, the total description count); `unverified`: anything not run or not reproduced (for example a Devin or Codex surface not available in the session); `next step`: the prompt id that follows (P3-07 or P3-04, whichever is unmerged and unblocked), and whether `sdd-process.md` had room for the extra bullet or needed the fold described in step 5. Then the proposed one-line CHANGELOG entry, for example:

`- \`sdd-spike\` (user-only) plus \`templates/doc-spike-report.md\`: a time-boxed \`spike/<topic>\` lane for game feel with no spec edits and no coverage gate, delivering media, a report and a proposed DGME/DTEC; \`spike/\` branches are never merged (branching-and-versioning §1, sdd-process entry point). Evidence: assessment §4.6, §6 E3; 9,451 spec lines with no movement code in stratics-client on 2026-10-06; check.sh: <N> skills (one more than main), descriptions N/7200 chars.`
