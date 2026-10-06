# P3-06 — Merge sdd-analyze and sdd-audit into one mechanical check

Phase: 3 · Repos: kit (agent-rules-kit) · Branch to create: feat/p3-06-sdd-check from main · Depends on: P1-08 · Effort: ~3 h

## Goal

Replace the two read-mostly SDD steps `sdd-analyze` (step 3, consistency report) and `sdd-audit` (step 4, quality checklist) with one skill `sdd-check` (step 3) run by the `researcher` subagent: step 1 is mechanical (the project spec validator's verdict plus the ten-row consistency table), step 2 is judgment (the audit checklist, moved to a `references/check-list.md` detail file), and both feed one report format. Renumber the SDD pipeline to 0..8 (constitution 0, specify 1, clarify 2, check 3, plan 4, tasks 5, implement 6, validate 7, to-card 8) in `sdd-process.md`, every `SDD step N —` description, every `# SDD N —` heading and the plugin index. Measurable result: `plugins/architect-sdd/skills/` has 8 folders instead of 9; the skill description budget drops from 6,803 to about 6,660 chars; a FEAT reaches `sdd-plan` after one forked check instead of two 50-line steps; `grep -rn "sdd-analyze\|sdd-audit" plugins platforms INDEX.md README.md` prints nothing.

## Why

- assessment §4.6: the SDD has ten steps and none closes the loop with the code; a ~9.5k-line spec for ~3k lines of new code and task tables with 128 `todo` rows after ~35 merged PRs show ceremony that is neither read nor updated ("spec theatre", Thoughtworks and the Spec Kit authors).
- assessment §6 item E4: `sdd-analyze` and `sdd-audit` can become a single mechanical check (`check_spec.py` plus a short checklist) executed by the `researcher`; two 50-line steps for 100-line FEATs is the ceremony to cut.
- kit `plugins/architect-sdd/skills/sdd-analyze/SKILL.md` is 48 lines and `sdd-audit/SKILL.md` is 50 lines (`wc -l`); both run on `agent: researcher` with `context: fork` and overlap on the FEAT graph; `sdd-analyze/SKILL.md:46` routes "quality gaps to `sdd-audit`" and `sdd-audit/SKILL.md:3` routes consistency back to `sdd-analyze`, so a FEAT pays two forks and two reports before planning.
- kit `plugins/architect-sdd/skills/sdd-tasks/SKILL.md:42` tells the executor to "Run `sdd-analyze` A8", an item id that does not exist in `sdd-analyze/SKILL.md:27-38` (the table has no ids); the merged skill fixes the dangling reference.
- The mechanical half already exists as code: the kit ships `platforms/ci/validations/check_spec.py` (docstring `:2`: `Usage: check_spec.py <spec-dir> <schemas-dir>`) and stratics-docs runs its synced copy as `python3 .github/spec-lint/check_spec.py docs/spec .github/spec-lint/schemas`; it checks frontmatter, ids, kinds and FEAT/REQ link agreement (`check_spec.py:139-188`), which is most of `sdd-analyze`'s table.

## Current state

Line numbers are from kit `claude/modest-mendel-7tq8a4` at `d7a3eff` (= `main` `ddd3ad2` plus one Unreleased CHANGELOG bullet, so `CHANGELOG.md:260` reads `:259` on main until that branch merges); P1-08 edits `sdd-tasks`, `sdd-implement` and `sdd-to-card` first, so re-grep every line below after rebasing on P1-08.

```
plugins/architect-sdd/skills/sdd-analyze/SKILL.md:3: description: SDD step 3 — cross-artifact consistency report. Use when FEAT/REQ/DEC/plan/tasks need gap checks. Not for spec quality (skill sdd-audit).
plugins/architect-sdd/skills/sdd-analyze/SKILL.md:17: # SDD 3 — Analyze
plugins/architect-sdd/skills/sdd-analyze/SKILL.md:27: | Check | Severity |
plugins/architect-sdd/skills/sdd-analyze/SKILL.md:42: Produce `# | severity | file:line | problem | suggestion`, counts by severity and whether the next SDD step is blocked. Save under `docs/spec/reports/` only when requested.
plugins/architect-sdd/skills/sdd-audit/SKILL.md:3: description: SDD step 4 — spec quality checklist. Use when a clarified FEAT needs testability, security and completeness checks. Not for consistency (skill sdd-analyze).
plugins/architect-sdd/skills/sdd-audit/SKILL.md:15:   - edit
plugins/architect-sdd/skills/sdd-audit/SKILL.md:18: # SDD 4 — Audit
plugins/architect-sdd/skills/sdd-audit/SKILL.md:26: ## 2. Audit testability and completeness
plugins/architect-sdd/skills/sdd-audit/SKILL.md:33: ## 3. Audit security and integrity
plugins/architect-sdd/skills/sdd-audit/SKILL.md:39: ## 4. Audit data, compatibility and operation
plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md:20:    specify → clarify → analyze → audit → plan → tasks → implement → validate → to-card
plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md:21:    FEAT/REQ  answers   gaps      quality  design  order   code/tests  verdict    issue
plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md:31: | 3 | `sdd-analyze` | related artifacts | consistency report |
plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md:32: | 4 | `sdd-audit` | clarified FEAT | quality checklist/gaps |
plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md:37: | 9 | `sdd-to-card` | FEAT | synchronized GitHub issue |
plugins/architect-sdd/skills/sdd-clarify/SKILL.md:3: description: SDD step 2 — resolve ambiguous FEAT criteria. Use when a FEAT has open questions or vague terms. Not for quality auditing (skill sdd-audit).
plugins/architect-sdd/skills/sdd-plan/SKILL.md:3: description: SDD step 5 — technical FEAT plan and decisions. Use when clarification and audit are complete. Not for task breakdown (skill sdd-tasks).
plugins/architect-sdd/skills/sdd-plan/SKILL.md:16: # SDD 5 — Plan
plugins/architect-sdd/skills/sdd-plan/SKILL.md:22: Require `status: clarified` and an audit without a security/integrity failure. Read the actual modules/files plus repository rules; do not infer structure from the desired design.
plugins/architect-sdd/skills/sdd-plan/SKILL.md:42: Do not add queue/cache/service/layer without demonstrated need. Ensure every criterion has a planned proof, then set `status: planned`, update History and run `sdd-analyze` with no critical/high findings.
plugins/architect-sdd/skills/sdd-tasks/SKILL.md:3: description: SDD step 6 — dependency-ordered implementation tasks. Use when a FEAT has an approved technical plan. Not for execution (skill sdd-implement).
plugins/architect-sdd/skills/sdd-tasks/SKILL.md:13: # SDD 6 — Tasks
plugins/architect-sdd/skills/sdd-tasks/SKILL.md:42: Every acceptance criterion appears in at least one task; every task covers a criterion or is explicitly infrastructure. Run `sdd-analyze` A8 and remove vague “implement the rest” rows.
plugins/architect-sdd/skills/sdd-implement/SKILL.md:3: description: SDD step 7 — task-by-task Red-Green-Refactor delivery. Use when a FEAT has ordered tasks. Not for completion verdicts (skill validate-implementation).
plugins/architect-sdd/skills/sdd-implement/SKILL.md:16: # SDD 7 — Implement
plugins/architect-sdd/skills/sdd-to-card/SKILL.md:3: description: SDD step 9 — sync a FEAT to GitHub Issues/Projects. Use when opening, updating or closing its card. Not for PR operations (skill github-cli).
plugins/architect-sdd/skills/sdd-to-card/SKILL.md:14: # SDD 9 — To Card
plugins/architect-sdd/INDEX.md:7: | `sdd-analyze` | SDD step 3 — cross-artifact consistency report. Use when FEAT/REQ/DEC/plan/tasks need gap checks. Not for spec quality (skill sdd-audit). |
plugins/architect-sdd/INDEX.md:8: | `sdd-audit` | SDD step 4 — spec quality checklist. Use when a clarified FEAT needs testability, security and completeness checks. Not for consistency (skill sdd-analyze). |
plugins/architect-sdd/templates/spec-feature.md:64: <!-- filled by sdd-audit (or a FEAT-000.checklist.md file) -->
plugins/architect-sdd/agents/researcher.md:16: You are the AI Kit research subagent. You answer one question and report back; you never edit files or run commands.
```

`plugins/core/AGENTS.md:55` routes `sdd-specify` → … → `validate-implementation` without naming the merged skills (`grep -c "sdd-analyze\|sdd-audit" plugins/core/AGENTS.md` prints 0): no edit there. `validate-implementation` lives in `plugins/quality-core/skills/validate-implementation/SKILL.md:3` and carries no `SDD step` prefix: no edit there either. New files: `plugins/architect-sdd/skills/sdd-check/SKILL.md` (new file; listed in `plugins/architect-sdd/INDEX.md`) and `plugins/architect-sdd/skills/sdd-check/references/check-list.md` (new file; skill subfolders are exempt from the index rule, `platforms/ci/validations/check_kit.py:731`, but the reference name must appear in `SKILL.md`, `check_kit.py:637`).

## Change

1. Create `plugins/architect-sdd/skills/sdd-check/SKILL.md` (kit, new file, 80 lines or fewer). Frontmatter verbatim (no `agents/openai.yaml`, no `disable-model-invocation`: the skill is user+model, so the parity rule at `check_kit.py:616` expects none of the three user-only markers):

```
---
name: sdd-check
description: SDD step 3 — mechanical spec check and quality checklist. Use when a clarified FEAT needs gap checks before planning. Not for ambiguity (skill sdd-clarify).
argument-hint: "FEAT-nnn | all [validator=<last line of check_spec.py>]"
triggers:
  - user
  - model
agent: researcher
context: fork
background: false
allowed-tools:
  - read
  - glob
  - grep
---
```

   Body outline, heading `# SDD 3 — Check`, then `Process: ../sdd-constitution/references/sdd-process.md. Read-only: this step edits no specification. Checklist: references/check-list.md.` Sections: `## 1. Mechanical checks` (a) validator verdict: the calling session runs `python3 .github/spec-lint/check_spec.py docs/spec .github/spec-lint/schemas` (the project copy synced from kit `platforms/ci/validations/check_spec.py`) and passes its last line as `validator=...`, because the `researcher` profile has no `exec` (`researcher.md:6-9`, `:16`); if absent, finding #1 is `high | validator not run; run <command>`; every `FAIL:` line becomes one `high` finding; (b) the consistency table copied verbatim from `sdd-analyze/SKILL.md:27-38` with a leading `Id` column `C1`..`C10`. `## 2. Judgment checks`: grade every item of `references/check-list.md` pass / fail / not-applicable with a `path:line` as evidence; a fail on a security or integrity item is `critical`. `## 3. Report` (one format): first line `validator: <verdict>`, then `# | step | severity | file:line | problem | suggestion`, counts by severity, and `blocked: yes|no` (critical or high blocks `sdd-plan`). Save under `docs/spec/reports/` only when requested; the calling session pastes the table into the FEAT `## Audit` section. `## 4. Route findings`: ambiguity to `sdd-clarify`, artifact corrections to the owning step, a kit-rule violation to a DEC or blocker. End with `Done when:` every finding cites `path:line`, the validator verdict is on line one, and the report states whether planning is blocked. Do not add `edit` or `exec` to `allowed-tools`.

2. Create `plugins/architect-sdd/skills/sdd-check/references/check-list.md` (kit, new file, 60 lines or fewer including frontmatter). Frontmatter verbatim:

```
---
description: Quality checklist for sdd-check step 2 (testability, security and integrity, data, compatibility and operation) with the grading rule.
kind: detail
---
```

   Body: heading `# Check list`, one line on grading (pass / fail / n-a, evidence `path:line`, security or integrity fail = critical), then three sections with the eleven bullets moved verbatim from `sdd-audit/SKILL.md:28-30`, `:34-37` and `:41-44`, numbered `Q1`..`Q11`: `## Testability and completeness` (Q1-Q3), `## Security and integrity` (Q4-Q7), `## Data, compatibility and operation` (Q8-Q11). No `verified`/`sources` (kind detail).

3. Delete `plugins/architect-sdd/skills/sdd-analyze/` and `plugins/architect-sdd/skills/sdd-audit/` (kit, both folders, each holds only `SKILL.md`).

4. Edit `plugins/architect-sdd/INDEX.md` (kit): remove lines 7-8; insert, in alphabetical order between the `sdd-a...` position and `sdd-clarify`, the row `| `sdd-check` | <description from step 1, verbatim> |`; update the `sdd-clarify`, `sdd-plan`, `sdd-tasks`, `sdd-implement` and `sdd-to-card` rows to the new descriptions of step 5 verbatim (`check_kit.py:792` fails on any difference).

5. Edit the sibling skills (kit). Descriptions (each 160 chars or fewer; keep the em dash the existing `SDD step N —` pattern uses): `sdd-clarify/SKILL.md:3` → `SDD step 2 — resolve ambiguous FEAT criteria. Use when a FEAT has open questions or vague terms. Not for gap checks (skill sdd-check).`; `sdd-plan/SKILL.md:3` → `SDD step 4 — technical FEAT plan and decisions. Use when clarification and check are complete. Not for task breakdown (skill sdd-tasks).`; `sdd-tasks/SKILL.md:3` → `SDD step 5 — ...` (rest unchanged); `sdd-implement/SKILL.md:3` → `SDD step 6 — ...` (rest unchanged); `sdd-to-card/SKILL.md:3` → `SDD step 8 — ...` (rest unchanged). Headings: `sdd-plan:16` → `# SDD 4 — Plan`, `sdd-tasks:13` → `# SDD 5 — Tasks`, `sdd-implement:16` → `# SDD 6 — Implement`, `sdd-to-card:14` → `# SDD 8 — To Card`. Bodies: `sdd-plan:22` → `Require `status: clarified` and an `sdd-check` report without a security/integrity failure. ...` (rest of the line unchanged); `sdd-plan:42` → `... update History and run `sdd-check` with no critical/high findings.`; `sdd-plan:44` → replace `consistency analysis is unblocked` with `the check is unblocked`; `sdd-tasks:42` → replace `Run `sdd-analyze` A8` with `Run `sdd-check` row C8 (criterion without task or task without criterion)`. `sdd-specify` and `sdd-constitution` descriptions stay (steps 1 and 0).

6. Edit `plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md` (kit). Replace lines 20-21 with:

```
   specify → clarify → check → plan → tasks → implement → validate → to-card
   FEAT/REQ  answers   gaps    design  order   code/tests  verdict    issue
```

   Replace rows 31-37 of the table with six rows: `| 3 | `sdd-check` | clarified FEAT + artifacts | validator, consistency and quality report |`, `| 4 | `sdd-plan` | checked FEAT | Plan + DECs; planned |`, `| 5 | `sdd-tasks` | Plan | ordered task rows |`, `| 6 | `sdd-implement` | Tasks | code/tests/docs; in-progress |`, `| 7 | `validate-implementation` | FEAT + delivery | READY/PARTIAL/NOT READY |`, `| 8 | `sdd-to-card` | FEAT | synchronized GitHub issue |`. Keep the file at 60 lines or fewer (58 today; P3-04 may have filled it to 60, and this change removes one line).

7. Edit `plugins/architect-sdd/templates/spec-feature.md:64` (kit) → `<!-- filled by the calling session from the sdd-check report (or a FEAT-000.checklist.md file) -->`. Keep the `## Audit` heading: all 52 stratics-docs FEAT files already carry it.

8. Grep the kit for the old names and fix every hit outside history: `grep -rn "sdd-analyze\|sdd-audit" plugins platforms INDEX.md README.md docs .github | grep -v "^docs/plans/"` must print nothing. Leave `CHANGELOG.md:260` (10.x history) and `docs/plans/` (assessment and prompts, historical) untouched.

9. `CHANGELOG.md` (kit), under `## [Unreleased]`: `### Changed` bullet (what: `sdd-check` replaces `sdd-analyze` and `sdd-audit`, steps renumbered 0..8 in `sdd-process.md`, descriptions, headings and index; why: assessment §4.6 and §6 E4, two forked read-only steps of 48 and 50 lines before every plan; proof: the four gate commands with their last lines and the description budget number), `### Removed` bullet (the two skill folders), `### Migration` bullet: `/sdd-analyze` and `/sdd-audit` no longer exist as user-invoked names; run `/sdd-check FEAT-nnn validator=<last line of check_spec.py>` instead; projects that mention the old names in `AGENTS.md`, FEAT `## Audit` comments or session notes should rename them at their next sync.

## Out of scope

- The task, implement and to-card flow bodies (issue per task, waves, model directive, task template): P1-08. Rebase on it; this prompt changes only the lines quoted above in those files.
- The `Regimes` section and entry-point rewrite of `sdd-process.md`: P3-04. Verification gates in `sdd-implement` and worktree cleanup: P3-07. `REVIEW.md` and `/code-review` in `validate-implementation`: P3-11. The spike lane: P3-05.
- Consolidating skills outside `architect-sdd` (P2-09) and the extras plugin (P2-10); the stale-path gate (P1-01).
- stratics-docs: the 51 FEAT files with `<!-- filled in by sdd-audit ... -->` and two session notes (`docs/sessions/2026-09-30-feat-002-analyze-audit.md`, `docs/sessions/2026-09-30-pendencias-reconciliacao.md`); its `AGENTS.md` has 0 hits today (P1-02 for stale kit citations; P2-15 for the regenerated agent configuration). Report them in `next step`, do not edit them.
- `plugins/core/AGENTS.md`, `plugins/quality-core/**`, `platforms/ci/validations/check_spec.py`, `platforms/ci/schemas/**`, `VERSION`, historical `CHANGELOG.md` entries.

## Acceptance criteria

- [ ] `test ! -d plugins/architect-sdd/skills/sdd-analyze && test ! -d plugins/architect-sdd/skills/sdd-audit && test -f plugins/architect-sdd/skills/sdd-check/SKILL.md && test -f plugins/architect-sdd/skills/sdd-check/references/check-list.md` exits 0; `ls plugins/architect-sdd/skills | wc -l` prints 8.
- [ ] `grep -rn "sdd-analyze\|sdd-audit" plugins platforms INDEX.md README.md docs .github | grep -v "^docs/plans/"` prints nothing; `grep -c "sdd-analyze\|sdd-audit" CHANGELOG.md` prints at least 2 (line 260 history plus the Migration bullet).
- [ ] `grep -ho "SDD step [0-9]" plugins/architect-sdd/skills/*/SKILL.md | sort` prints `SDD step 0`, `1`, `2`, `3`, `4`, `5`, `6`, `8` (no 7: `validate-implementation` carries no step prefix, no 9); `grep -ho "^# SDD [0-9]" plugins/architect-sdd/skills/*/SKILL.md | sort` prints the same eight numbers.
- [ ] `grep -c "| \`sdd-check\` |" plugins/architect-sdd/INDEX.md` prints 1; `grep -c "sdd-check" plugins/architect-sdd/skills/sdd-constitution/references/sdd-process.md` prints 1; `grep -c "| 9 |" ...sdd-process.md` prints 0; `grep -c "| 8 | \`sdd-to-card\`" ...sdd-process.md` prints 1; `wc -l ...sdd-process.md` prints 60 or less.
- [ ] `grep -c "sdd-check" plugins/architect-sdd/skills/sdd-plan/SKILL.md` prints 2; `grep -c "sdd-check\` row C8" plugins/architect-sdd/skills/sdd-tasks/SKILL.md` prints 1; `grep -c "sdd-check" plugins/architect-sdd/templates/spec-feature.md` prints 1.
- [ ] `wc -l plugins/architect-sdd/skills/sdd-check/SKILL.md` prints 80 or less; `wc -l plugins/architect-sdd/skills/sdd-check/references/check-list.md` prints 60 or less; `grep -c "^kind: detail$" plugins/architect-sdd/skills/sdd-check/references/check-list.md` prints 1; `grep -c "check-list.md" plugins/architect-sdd/skills/sdd-check/SKILL.md` prints at least 1; `grep -c "^  - exec\|^  - edit" plugins/architect-sdd/skills/sdd-check/SKILL.md` prints 0; `test ! -e plugins/architect-sdd/skills/sdd-check/agents` exits 0.
- [ ] The description budget check below prints 7200 or less (6660 when the descriptions above are adopted verbatim):

```
python3 - <<'PY'
import re,glob;print(sum(len(re.search(r'^description:\s*(.*)$',open(f).read(),re.M).group(1).strip().strip('"')) for f in glob.glob('plugins/*/skills/*/SKILL.md')))
PY
```

- [ ] `platforms/tools/check.sh` ends with the OK summary; `platforms/tools/smoke.sh` exits 0; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` prints `OK`; `python3 platforms/ci/validations/check_kit.py --links` exits 0.
- [ ] `git diff main --stat -- VERSION plugins/core/AGENTS.md plugins/quality-core platforms/ci/schemas platforms/ci/validations/check_spec.py` is empty.
- [ ] `sed '/^## \[10.1.0\]/,$d' CHANGELOG.md | grep -c "sdd-check"` prints at least 2.

## Conventions

- Everything committed is in English; plain ASCII punctuation in new prose, except the em dash kept in the `SDD step N —` and `# SDD N —` patterns the sibling skills already use.
- No layout or path change: the 10.x layout is frozen; skills stay flat at `plugins/architect-sdd/skills/<name>/SKILL.md` with references under `references/`; template names keep matching `^(spec|doc|project|kit)-[a-z0-9-]+\.md$`.
- `VERSION` untouched; `CHANGELOG.md` gets `## [Unreleased]` entries with what, why and proof.
- `plugins/architect-sdd/INDEX.md` lists every entry of `skills/` by name and copies each skill description verbatim into its table row (`check_kit.py:788-792`).
- Skill description 40-160 chars in the form `<what>. Use when <trigger>. Not for <neighbor> (skill <x>).`; all descriptions together 7,200 chars or fewer (6,803 today); `SKILL.md` 80 lines or fewer; references 60 lines or fewer with frontmatter `description` + `kind: detail` (no `verified`/`sources`).
- `allowed-tools` lowercase (`read`, `glob`, `grep`); subagent skill = `agent: researcher` + `context: fork` + `background: false` (`check_kit.py:595`); user+model triggers, so no `disable-model-invocation` and no `agents/openai.yaml` (`check_kit.py:616`). The `researcher` profile in `plugins/architect-sdd/agents/researcher.md` is not edited.
- Conventional Commits with Refs, for example `feat(architect-sdd): merge sdd-analyze and sdd-audit into sdd-check; renumber SDD steps 0..8` and `Refs: docs/plans/2026-10-kit-assessment/prompts/p3-06-merge-analyze-audit.md`; PR body = What / Why / How I tested (literal output) / Refs, plus the kit `.github/PULL_REQUEST_TEMPLATE.md` checklist.
- Gates (kit): `platforms/tools/check.sh`; `platforms/tools/smoke.sh`; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`; `python3 platforms/ci/validations/check_kit.py --links`.

## Report back

Final message in three blocks: `done` (every path created, edited or deleted, each Acceptance criteria command with its literal result, the description budget number, the PR URL), `unverified` (anything not run, for example a `check_spec.py` run against a real project spec, or the P1-08 rebase if P1-08 is not merged), `next step` (stratics-docs still names `sdd-audit` in 51 FEAT `## Audit` comments and two session notes (`docs/sessions/2026-09-30-feat-002-analyze-audit.md`, `docs/sessions/2026-09-30-pendencias-reconciliacao.md`): P1-02/P2-15 or a follow-up; P3-07 adds the verification gates to `sdd-implement`). End with the proposed one-line CHANGELOG entry, for example: `- SDD: sdd-check (step 3, researcher fork, read-only) replaces sdd-analyze and sdd-audit: validator verdict + consistency table (C1-C10) + quality checklist (Q1-Q11, references/check-list.md), one report; steps renumbered 0..8 in sdd-process.md, descriptions, headings and INDEX. Evidence: assessment §4.6, §6 E4; two forked steps of 48 and 50 lines before every plan; budget 6,803 → 6,660 chars.`
