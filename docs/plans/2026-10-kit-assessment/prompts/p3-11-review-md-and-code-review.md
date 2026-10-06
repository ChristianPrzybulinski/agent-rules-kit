# P3-11 — REVIEW.md template and /code-review in validate-implementation

Phase: 3 · Repos: kit · Branch to create: feat/p3-11-review-md-and-code-review from main · Depends on: P3-07 (it adds one bullet to `validate-implementation` §2, so §3 of that file shifts by one line; this prompt anchors on sentences, never on a line number inside that file) · Effort: ~2 h

## Goal

Give every project repository a ready-to-copy `REVIEW.md` with the kit's review criteria in the form Anthropic's hosted Claude Code Review reads (a freeform Markdown file at the repository root, Team/Enterprise plans), and make `validate-implementation` run `/code-review` as a background subagent before it issues a verdict when the executor is Claude Code. After this change, the same five criteria (scope, correctness, architecture, security, docs) exist once in a de-projected form that any reviewer, human or hosted, can apply, and a Claude Code validation never ends without an independent correctness pass. Measurable result: `platforms/kits/github/REVIEW.md` exists at or under 40 lines, is listed in `platforms/kits/github/README.md` and `docs/projects.md`, `validate-implementation/SKILL.md` stays at or under 80 lines with its description unchanged, and all four kit gates pass.

## Why

- assessment §5, verification row: Anthropic's `best-practices` prescribes "if you cannot verify, do not ship" with `/goal`, a Stop-hook gate, an adversarial subagent that sees only the diff and the criteria, and `/code-review`; verdict "correct" for `reviewer` and `validate-implementation`, but neither mentions `/code-review`. `grep -rc 'code-review' plugins/quality-core/` prints 0 for every file on 2026-10-06.
- assessment §7 item N7: "`REVIEW.md` per repo (if the Team/Enterprise plan with hosted Code Review is used) with the criteria that today are in `doc-review-checklist.md`, and `/code-review` as a step of `validate-implementation` in Claude Code."
- assessment §5, Code Review row: the hosted review "reads `REVIEW.md`" and is the only review surface that runs without the kit installed on a machine, so the criteria must reach it as a committed file, not as a plugin skill.
- The kit's only review criteria are project-bound: `plugins/quality-core/templates/doc-review-checklist.md:11` demands `JaCoCo 100% + PITest ≥80%`, `:12` names `inventory/economy/reward`, `:13` names `protocol_version`, `:26` names `FEAT status`. A Godot-only or docs-only repository cannot use it as written, and no Stratics repository has a `REVIEW.md` today (`ls stratics-client/REVIEW.md stratics-server/REVIEW.md stratics-docs/REVIEW.md` finds nothing on 2026-10-06).
- Verified on 2026-10-06 against code.claude.com/docs/en/code-review: `REVIEW.md` "is a file at your repository root that tailors Code Review to your repo", "freeform markdown", read by the hosted review (Team and Enterprise, research preview); the local `/code-review` command "runs as a background subagent with its own context window", "follows your `CLAUDE.md` like any Claude Code session, but it doesn't read `REVIEW.md`", and "reports correctness bugs". Re-verify these four facts against that page before relying on them; the page carries no publication date.

## Current state

- `platforms/kits/github/` holds `CODEOWNERS`, `PULL_REQUEST_TEMPLATE.md`, `README.md`, `dependabot.yml`, `labels.json`, `scripts/`, `workflows/`; no `REVIEW.md`. (new file) `platforms/kits/github/REVIEW.md`, listed by `platforms/kits/github/README.md` (the folder's index; `check_kit.py` fails any entry of `platforms/kits/github/` missing from it).
- `platforms/kits/github/README.md:7-14` is the destination table; `:13-14`:
  ```text
  | `labels.json` | reference for `scripts/labels-sync.sh` |
  | `scripts/labels-sync.sh` | run from anywhere inside the repo: `bash platforms/kits/github/scripts/labels-sync.sh` |
  ```
  `:16` is `## Notes`; `:21` is the last note (`gitleaks.yml` needs `fetch-depth: 0`).
- `docs/projects.md:15`:
  ```text
  | `.github/PULL_REQUEST_TEMPLATE.md`, `CODEOWNERS`, `dependabot.yml`, labels | `platforms/kits/github/` | ditto + `scripts/labels-sync.sh` |
  ```
- `platforms/kits/INDEX.md:9`:
  ```text
  | `github/` | workflows (spec-lint, gitleaks, ci-java, ci-godot), PR template, CODEOWNERS, labels + sync, dependabot | every new repo |
  ```
- `plugins/quality-core/templates/doc-review-checklist.md` (34 lines) stays byte-identical. Its sections `:5` `## Scope`, `:9` `## Correctness`, `:15` `## Architecture`, `:20` `## Security`, `:24` `## Docs` are the source of the five criteria; `:3` reads `Mark only what was **observed**. Non-applicable item: `n/a`. Unverified item: leave it empty and say why at the end.`
- `plugins/quality-core/skills/validate-implementation/SKILL.md` (68 lines on main; 69 after P3-07). Frontmatter `:3` description `Completion verdict against a request or FEAT. Use when asking “is it done?” or preparing a PR. Not for fixing failures (skill sdd-implement).` and `:8-10` `agent: reviewer` / `context: fork` / `background: false` stay unchanged, so `plugins/quality-core/INDEX.md:8` stays unchanged. §3 today (`:34-44`):
  ```text
  ## 3. Run canonical gates

  Read the repository's `AGENTS.md` and README for commands. Kit fallbacks:

  | Stack | Gate |
  |---|---|
  | Java/Maven | `./mvnw -q spotless:check verify` |
  | Godot | `godot --path . --headless --quit` plus the project test runner |
  | Docs/spec | `platforms/tools/check.sh` or project spec lint |

  Capture the literal failing excerpt; never replace it with “some tests failed.”
  ```
  §5 verdict block (`:52-61`) has `Gates: <command> → OK | FAILED (<literal excerpt>)` and the criterion table; it stays unchanged.
- `plugins/quality-core/agents/reviewer.md` (31 lines) stays byte-identical.
- `CHANGELOG.md:5` is `## [Unreleased]` with `### Added` (`:7`) and `### Changed` (`:11`) already present.
- Measured on 2026-10-06: 43 skills, description total 6,803 chars (`check.sh` prints the figure; budget 7,200 at `platforms/ci/validations/check_kit.py:25`); `SKILL_MAX_LINES = 80` at `:26`; the plugin template name regex at `:694` applies only to `plugins/*/templates/`, so `REVIEW.md` under `platforms/kits/github/` needs no `doc-` prefix.

## Change

1. kit: create `platforms/kits/github/REVIEW.md` (new file), at most 40 lines, verbatim:
   ```markdown
   # Review instructions

   Review criteria for this repository. Read by Anthropic's hosted Claude Code Review (Team/Enterprise) and by any reviewer, human or agent. Flag only gaps that affect correctness or the stated criteria; nits are optional. Report at most five nits; mention the rest as a count. Every finding cites `path:line` in the diff, not an inference from a name.

   ## Important means

   A finding that breaks a criterion below, breaks behavior, leaks data or blocks a rollback. Style, naming and refactoring suggestions are nits at most.

   ## Scope
   - The PR does one thing; Conventional Commit title; the body links the issue, FEAT, REQ or DEC it implements.
   - Changed paths stay inside the task's Files cell (or the issue's stated scope); anything else is a separate issue or DEBT.

   ## Correctness
   - Each acceptance criterion has a named test; the sad path (invalid input, failure, timeout) is covered.
   - A proof must be able to fail: a gate that passes on zero tests or empty input is not proof.
   - A changed contract (schema, message, API) bumps its version and updates fixtures on every side.

   ## Architecture
   - Dependencies point inward; domain code has no framework or engine import.
   - The server validates everything that changes state; the client only pre-validates UX.
   - No new pattern without a present problem; a trade-off is recorded as a decision.

   ## Security
   - No secret or personal data in code, logs or error messages; input validated at the boundary.
   - Authorization checked per action and per entity on every touched endpoint or handler.
   - SQL is parameterized; no string-built queries.

   ## Docs
   - CHANGELOG `Unreleased` entry; README when a command changed; doc comment on new public API.
   - Spec status updated when the repository keeps one (`docs/spec/`); incomplete work recorded as DEBT or behind a flag.

   ## Do not report
   - Anything CI already enforces: formatting, lint, type errors, secret scanning.
   - Generated files (`*.uid`, `*.import`, `.godot/`, lockfiles, `target/`).
   ```
2. kit: edit `platforms/kits/github/README.md`. Insert one row after the `PULL_REQUEST_TEMPLATE.md` row (`:10`), verbatim: `| `REVIEW.md` | `REVIEW.md` at the repository root (read by hosted Claude Code Review; also the checklist for any reviewer) |`. Append one note after `:21`, verbatim: `- `REVIEW.md` holds the five review criteria of `plugins/quality-core/templates/doc-review-checklist.md` without project-specific gates; a project adds its own gates (coverage, mutation score, contract version field) under the matching heading. Hosted Claude Code Review (Team/Enterprise) reads it from the repository root; the local `/code-review` command does not (it reads `CLAUDE.md`); verify both facts against code.claude.com/docs/en/code-review before relying on them.`
3. kit: edit `docs/projects.md:15`: change the first cell to `| `.github/PULL_REQUEST_TEMPLATE.md`, `CODEOWNERS`, `dependabot.yml`, labels, root `REVIEW.md` |` and the third cell to `| ditto + `scripts/labels-sync.sh`; `REVIEW.md` is copied to the repository root, not to `.github/` |`. The second cell stays `platforms/kits/github/`.
4. kit: edit `platforms/kits/INDEX.md:9`: in the Contents cell, replace `labels + sync, dependabot` with `labels + sync, dependabot, root REVIEW.md`.
5. kit: edit `plugins/quality-core/skills/validate-implementation/SKILL.md` §3. Leave the gate table and the sentence `Capture the literal failing excerpt; never replace it with “some tests failed.”` byte-identical, and insert directly after that sentence one blank line and this paragraph, verbatim:
   ```text
   In Claude Code (Claude-specific) also run `/code-review <base>...HEAD` on the pushed head before the verdict; it runs as a background subagent and reports correctness bugs, so wait for it and keep the next step unblocked. Confirm each finding at `path:line` on the clean checkout; a confirmed finding becomes a `missing` or `partial` row of the criterion table (or a `Gates:` line `code-review → FAILED (<finding>)` when it belongs to no criterion); an unconfirmed one goes under `Unverified`. In Devin or any other executor, apply the repository `REVIEW.md` (kit copy: `platforms/kits/github/REVIEW.md`) by hand instead. `/code-review` reads `CLAUDE.md`, not `REVIEW.md`; verify the command syntax against code.claude.com/docs/en/code-review before relying on it.
   ```
   Result: 71 lines on top of P3-07's 69 (72 if P3-07 is not merged yet, which changes nothing else). Frontmatter, §1, §2, §4, §5 and the `Done when:` line stay unchanged.
6. kit: `CHANGELOG.md`, under `## [Unreleased]` / `### Added`, add one bullet (text in Report back). No `VERSION` change.
7. Prove the new step is reachable before committing: in a Claude Code session on the kit branch, run `/code-review main...HEAD` and paste the first three lines of its output in the PR body. If `claude` is not available, paste the literal `command not found` under Unverified.

## Out of scope

- `plugins/quality-core/agents/reviewer.md` and `plugins/quality-core/templates/doc-review-checklist.md`: byte-identical (the checklist stays the author-facing form; P3-08 complements both with `loop-review`).
- The Godot gate row `godot --path . --headless --quit` in `validate-implementation/SKILL.md` and `reviewer.md:22`: P1-06.
- The clean-checkout worktree cleanup bullet in §2 of `validate-implementation`: P3-07.
- `sync-project.sh` copying `REVIEW.md` or `CLAUDE.md` into a repository: P2-04 (CLAUDE.md and settings) and P2-05/P2-06; this task ships the template only and documents the copy by hand.
- Applying `REVIEW.md` to stratics-client, stratics-server or stratics-docs: P2-15.
- No hook (the validator accepts only `PreToolUse`), no new skill, no description change, no `skillOverrides` or settings file.

## Acceptance criteria

- [ ] `git diff --stat main` lists exactly six files: `platforms/kits/github/REVIEW.md`, `platforms/kits/github/README.md`, `platforms/kits/INDEX.md`, `docs/projects.md`, `plugins/quality-core/skills/validate-implementation/SKILL.md`, `CHANGELOG.md`.
- [ ] `wc -l platforms/kits/github/REVIEW.md` → at most `40`; `grep -c '^## ' platforms/kits/github/REVIEW.md` → `7` (Important means, Scope, Correctness, Architecture, Security, Docs, Do not report).
- [ ] `grep -c 'Flag only gaps that affect correctness or the stated criteria; nits are optional' platforms/kits/github/REVIEW.md` → `1`; `grep -c 'path:line' platforms/kits/github/REVIEW.md` → `1`; `grep -c 'parameterized' platforms/kits/github/REVIEW.md` → `1`.
- [ ] `grep -cE 'JaCoCo|PITest|protocol_version|inventory|FEAT-|Stratics|stratics' platforms/kits/github/REVIEW.md` → `0` (de-projected).
- [ ] `grep -c 'REVIEW.md' platforms/kits/github/README.md` → at least `3`; `grep -c 'REVIEW.md' docs/projects.md` → `2`; `grep -c 'REVIEW.md' platforms/kits/INDEX.md` → `1`.
- [ ] `grep -c '/code-review <base>...HEAD' plugins/quality-core/skills/validate-implementation/SKILL.md` → `1`; `grep -c 'Claude-specific' plugins/quality-core/skills/validate-implementation/SKILL.md` → `1`; `grep -c 'reads `CLAUDE.md`, not `REVIEW.md`' plugins/quality-core/skills/validate-implementation/SKILL.md` → `1`.
- [ ] `grep -c 'Capture the literal failing excerpt' plugins/quality-core/skills/validate-implementation/SKILL.md` → `1` (anchor survives); `wc -l plugins/quality-core/skills/validate-implementation/SKILL.md` → `71` (or `72` without P3-07), at most 80.
- [ ] `sed -n 1,16p plugins/quality-core/skills/validate-implementation/SKILL.md | diff - <(git show main:plugins/quality-core/skills/validate-implementation/SKILL.md | sed -n 1,16p)` → no output (frontmatter unchanged); `git diff --stat main -- plugins/quality-core/INDEX.md plugins/quality-core/agents plugins/quality-core/templates` → empty.
- [ ] `grep -c '^## \[Unreleased\]' CHANGELOG.md` → `1`; `grep -c 'REVIEW.md' CHANGELOG.md` → at least `1`.
- [ ] `git diff main -- platforms/kits/github/REVIEW.md plugins/quality-core/skills/validate-implementation/SKILL.md | grep -c '/Users/\|/home/'` → `0`.
- [ ] `platforms/tools/check.sh` → ends with `check: ok (12 plugins, 43 skills, ...)`; the description total stays 6,803. A `broken link` failure in a `docs/plans/2026-10-kit-assessment/prompts/*.md` file other than this one is pre-existing: report it, do not fix it.
- [ ] `platforms/tools/smoke.sh` → exit 0.
- [ ] `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` → `OK`.
- [ ] `python3 platforms/ci/validations/check_kit.py --links` → `check: ok`.

## Conventions

- Everything committed is in English; no layout or path change (the 10.x layout is frozen: `REVIEW.md` lives under `platforms/kits/github/` beside the other GitHub templates); `VERSION` untouched.
- `CHANGELOG.md` gets a `## [Unreleased]` entry written with evidence (what, why, proof).
- `INDEX.md` or `README.md` of every touched folder lists every entry by name: `platforms/kits/github/README.md` (the new file), `platforms/kits/INDEX.md` (contents cell); `plugins/quality-core/INDEX.md` stays unchanged because no skill description changes and its table must still match the frontmatter verbatim.
- `SKILL.md` at most 80 lines; `validate-implementation` keeps `triggers: [user, model]`, `agent: reviewer`, `context: fork`, `background: false` and lowercase `allowed-tools` (read, grep, glob, exec).
- `REVIEW.md` is not a plugin template, so the `^(spec|doc|project|kit)-` name rule does not apply; do not move it into `plugins/*/templates/`.
- Backticked paths in `SKILL.md` are resolved by `check_kit.py` (`platforms/` and `plugins/` prefixes): the new paragraph cites `platforms/kits/github/REVIEW.md`, so create the file in the same commit.
- Hooks validator accepts only `PreToolUse` with timeout at most 10: this task adds no hook.
- Conventional Commits with `Refs`: `feat(quality-core): REVIEW.md template and /code-review step in validate-implementation` with `Refs: P3-11, assessment N7`.
- PR body = What / Why / How I tested (literal output of the four gates and of step 7) / Refs.
- Gates: `platforms/tools/check.sh`; `platforms/tools/smoke.sh`; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`; `python3 platforms/ci/validations/check_kit.py --links`.

## Report back

Final message, in this order:

1. Done: the six touched paths with final line counts; every acceptance command with its literal result (not "passed"); the first three lines of the `/code-review` output from step 7.
2. Unverified: anything you could not run (`claude plugin validate` when `claude` is not on PATH, which `check.sh` reports as skipped; `/code-review` when not in Claude Code) and the two Code Review facts (hosted review reads `REVIEW.md`; local `/code-review` does not) if you could not reach code.claude.com/docs/en/code-review.
3. Next step: the PR URL, or the smallest blocker that stops the PR; then P2-15 to copy `REVIEW.md` into the three Stratics repositories.
4. Proposed CHANGELOG line (one bullet under `### Added`): `platforms/kits/github/REVIEW.md`: the five review criteria (scope, correctness, architecture, security, docs) in the repository-root form hosted Claude Code Review reads, de-projected from `doc-review-checklist.md` (no coverage numbers, contract fields or FEAT status), with "flag only gaps that affect correctness or the stated criteria; nits are optional"; `validate-implementation` §3 runs `/code-review` as a background subagent in Claude Code before the verdict and folds confirmed findings into the criterion table. Evidence: `grep -rc code-review plugins/quality-core/` printed 0 on 2026-10-06; no Stratics repository had a `REVIEW.md`; assessment §5 verification row and §7 N7.
