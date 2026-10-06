# P3-07 — Verification gates in sdd-implement and worktree cleanup in reviewer

Phase: 3 · Repos: kit · Branch to create: feat/p3-07-verification-gates-and-worktree-cleanup from main · Depends on: P3-06 (same `sdd-implement/SKILL.md`; it only changes that file's `SDD step N` description and H1), P1-08 (P1-08 replaces §1, §4 and the commit step of §2 of `sdd-implement`; it keeps the sentence `Run the task's proof literally and summarize output in History.` verbatim, which is this prompt's only anchor, never a step number). Execute before P3-11 (it inserts two lines into §3 of `validate-implementation`) · Effort: ~2 h

## Goal

Make every `sdd-implement` task end at a verification gate instead of at a claim, and make every clean-checkout review leave the repository as it found it. After this change, `sdd-implement` §2 tells the executor how the proof becomes a gate (in Claude Code a user-set `/goal` condition keeps the session running until the proof output shows exit 0; in Devin the Proof section of the PR body (§4) is re-run by the reviewer), and demands a screenshot or GIF for a visual change; `reviewer` and `validate-implementation` always run `git worktree remove --force` plus `git worktree prune` after the clean checkout, even when a proof fails. Measurable result: `git worktree list` in a reviewed repository has the same number of lines before and after a review (Stratics had 53 leftover worktrees after one batch), the three files stay at or under 80 lines, no skill description or index changes, and all four kit gates pass.

## Why

- assessment §5, verification row: Anthropic's `best-practices` prescribes "if you cannot verify, do not ship" with `/goal`, a Stop-hook gate and an adversarial reviewer; verdict "correct; `/goal` and Stop-gate are missing in `sdd-implement`". The skill stops at `Run the task's proof literally and summarize output in History.` (`plugins/architect-sdd/skills/sdd-implement/SKILL.md:29`), so a session can end with a failing proof recorded as prose.
- assessment §6 item C3: "End each task with `/goal "<task proof> passes"` (or a Stop-hook that runs the proof) and, for a visual change, require a screenshot/GIF. Include worktree cleanup in `reviewer`/`validate-implementation` (`git worktree remove`; `git worktree prune`)".
- assessment §4.10: "`reviewer` creates worktrees (`git worktree add --detach`) and does not remove them; the project accumulated 53 worktrees and 61 orphan branches." Source fact: stratics-docs `docs/spec/decisions/DPRO-011-orchestrated-review-loop.md:122`: "[FACT] After batch-20261004-141711, 61 merged branches and 53 worktrees were left behind."
- Both review procedures create the worktree and never mention removal: `plugins/quality-core/agents/reviewer.md:21` and `plugins/quality-core/skills/validate-implementation/SKILL.md:31` (grep `worktree remove` over `plugins/quality-core/` returns 0 lines on 2026-10-06). The kit already documents the commands in `plugins/core/skills/parallelize/references/worktrees.md:19-20`, but nothing in the review path uses them.
- The Stratics PR templates already carry the Devin-side gate: stratics-client `.github/PULL_REQUEST_TEMPLATE.md:18-27` has a `## Proof` section with a ```` ```proof ```` block whose every line "must exit 0 when the loop re-runs it on a clean checkout of the pushed head", and `:11` asks for "a GIF/screenshot when the change is visual". The kit skill does not know this gate exists.
- The kit's own Godot template asks for the picture but the SDD skill does not: `plugins/dev-godot/templates/project-agents-godot-2d.md:77`: "Conventional Commits; PR with a GIF/screenshot when the change is visual."

## Current state

- Line numbers below are those of `main` on 2026-10-06, before P1-08; after P1-08 anchor on the quoted sentences only (P1-08 replaces §1, §4 and the commit step of §2 of `sdd-implement`; it keeps the sentence `Run the task's proof literally and summarize output in History.` verbatim, which is this prompt's only anchor, so `:45` and the exact line counts no longer hold).
- `plugins/architect-sdd/skills/sdd-implement/SKILL.md` (45 lines; description at `:3` stays unchanged, so `plugins/architect-sdd/INDEX.md:11` stays unchanged). Lines 24-33:
  ```text
  ## 2. Execute each task

  1. Mark `doing` and read every named file.
  2. For behavior, run/write the test first; it must fail for the intended reason.
  3. Implement the minimum, make the test green, then refactor.
  4. Run the task's proof literally and summarize output in History.
  5. Review conformance to task/criterion before code quality; a scope finding returns to implementation.
  6. Commit atomically as `feat(scope): <task>` with `Refs: FEAT-nnn`; mark `done`.

  A dependency/product/rule blocker becomes `blocked` with reason; never invent a workaround. Move only to an independent task.
  ```
  `:45`: `Done when: all tasks and proofs are recorded, full gates pass, validation is READY, and incomplete merged behavior is safely flagged with expiry handling.`
- `plugins/quality-core/agents/reviewer.md` (31 lines; `allowed-tools` read/grep/glob/exec at `:4-8` and `tools` Read/Grep/Glob/Bash at `:9-13` stay unchanged). `:21`:
  ```text
  2. Evidence at the pushed head: review the pushed commit, never someone's working tree. Check it out clean (`git worktree add --detach <tmp> <sha>`). The author's report, from a human or an agent, is a claim: re-run there every proof command it cites. A result that no command reproduces on that checkout is unverified. A proof that fails there is a blocker, even when the report says it passed. A proof that cannot fail (zero tests, zero schemas, an empty input set) proves nothing, so check that it would fail on a broken case.
  ```
  `:25-31` is the report format (`## Report (at most 80 lines)`, Verdict, Gates, Proof re-run, Findings table, Unverified); it stays unchanged.
- `plugins/quality-core/skills/validate-implementation/SKILL.md` (68 lines; description at `:3` unchanged, so `plugins/quality-core/INDEX.md:8` unchanged). `:31`:
  ```text
  - Validate the pushed head on a clean checkout (`git worktree add --detach <tmp> <sha>`); local uncommitted state never counts. Re-run there every proof command the author's report or PR lists. A claimed result that no command reproduces there is unverified; one that fails there makes the verdict `NOT READY`.
  ```
  `:52-61` is the verdict block; it stays unchanged.
- `CHANGELOG.md:5` is `## [Unreleased]` with `### Added` and `### Changed` subsections already present; add under `### Changed`.
- Measured on 2026-10-06: 43 skills, descriptions total 6,803 chars (budget 7,200, `platforms/ci/validations/check_kit.py:25`); `SKILL_MAX_LINES = 80` at `:26`; the hooks validator at `:452` rejects any event other than `PreToolUse` (until P2-07, which also accepts `PostToolUse`).

## Change

1. kit: edit `plugins/architect-sdd/skills/sdd-implement/SKILL.md` §2. Keep steps 1-4 as they are. Insert one new step directly after the step that reads `Run the task's proof literally and summarize output in History.` and renumber the two steps that follow it (conformance review, atomic commit). New step, verbatim:
   ```text
   5. Gate on the proof before moving on. In Claude Code (Claude-specific) the user sets `/goal <proof command> exits 0` before the task starts (the agent cannot invoke the built-in command itself); the goal evaluator re-checks the transcript after every turn until the proof output shows exit 0, so paste the literal proof output. Verify the syntax against code.claude.com/docs/en/goal before relying on it. In Devin or any other executor, the Proof section of the PR body (§4) is the gate: the reviewer re-runs every line on a clean checkout and a failing line blocks. For a visual change (scene, UI, shader, animation) the PR carries a screenshot or GIF; `--headless` renders nothing, so capture from the editor or run the capture under `xvfb-run` in CI (verify against the Godot command-line docs before relying on it).
   ```
   Then, on the line that starts with `Done when:`, append `and gated` after the word `recorded` (or, if P1-08 reworded that line, insert `each proof gated,` as the first clause after `Done when:`). Result: one line more than before the change, at most 80; nothing else in the file changes. If `sdd-implement/SKILL.md` is already at 80 lines after P1-08, fold the new step onto the proof step as one numbered line (`4. Run the task's proof literally and summarize output in History, then gate on it: ...`) and report the fold under Unverified. Do not add a `/goal` line anywhere else and do not mention Stop hooks in the skill.
2. kit: edit `plugins/quality-core/agents/reviewer.md:21`. Replace, on that line, the fragment that reads
   ```text
   <sha>`). The author's report
   ```
   with this fragment (same line, so the new text sits between the closing parenthesis and `The author's report`):
   ```text
   <sha>`). Create `<tmp>` with `mktemp -d`, and always finish with `git worktree remove --force <tmp> && git worktree prune`, even when a proof fails or the review aborts (`trap` it on exit in a shell); before you start, `git worktree list`; remove only a leftover whose path is a `mktemp` directory from an earlier review, never a worktree you did not create, and report any other extra worktree under Unverified. A review that leaves a worktree behind is not finished. The author's report
   ```
   The rest of step 2 (claims, re-runs, proofs that cannot fail) stays verbatim. The file stays at 31 lines; `allowed-tools`, `tools` and the `## Report` section do not change.
3. kit: edit `plugins/quality-core/skills/validate-implementation/SKILL.md`. Leave line 31 byte-identical and add one new bullet directly after it (new line 32), verbatim:
   ```text
   - Create `<tmp>` with `mktemp -d` and always finish with `git worktree remove --force <tmp> && git worktree prune`, even when a proof fails or the validation aborts; before you start, `git worktree list`; remove only a leftover whose path is a `mktemp` directory from an earlier validation, never a worktree you did not create, and report any other extra worktree under Unverified. A validation that leaves a worktree behind is not finished.
   ```
   Result: 69 lines. §5 (verdict block) and the frontmatter do not change.
4. kit: `CHANGELOG.md`, under `## [Unreleased]` / `### Changed`, add one bullet in the existing style (what, why, evidence). Proposed text is in Report back.
5. No index edit: no file is created or renamed and no description changes, so `plugins/architect-sdd/INDEX.md` and `plugins/quality-core/INDEX.md` must show an empty diff.
6. Prove the cleanup sequence once, in your kit clone, before committing (this is the behaviour the new text prescribes, including the failure path):
   ```bash
   before=$(git worktree list | wc -l)
   tmp=$(mktemp -d)
   trap 'git worktree remove --force "$tmp"; git worktree prune' EXIT
   git worktree add --detach "$tmp" HEAD
   (cd "$tmp" && false) || echo "proof failed, cleanup still runs"
   echo "before=$before"
   ```
   Run it as one script fed on stdin (`bash -s <<'EOF' … EOF`; a `bash -c '...'` wrapper breaks the single quotes of the `trap` line) so the EXIT trap fires when the script ends, then `git worktree list | wc -l` must print the same number as the `before=` line. Paste both numbers in the PR body.

## Out of scope

- No hook of any kind: no Stop hook, no PostToolUse hook, no change to `plugins/core/hooks/hooks.json` (the validator accepts `PreToolUse`, plus `PostToolUse` since P2-07; hooks are owned by P1-07 and P2-07).
- The Godot gate on `reviewer.md:22` and in the `validate-implementation` §3 table (line 41 on main, 42 after your bullet) is owned by P1-06; leave whatever P1-06 put there byte-identical.
- `platforms/kits/github/PULL_REQUEST_TEMPLATE.md` has no Proof section today (26 lines: What / Why / How I tested / Checklist / Refs); do not add one here, name it under Next step as a follow-up.
- The issue-per-task flow, waves, model directive and task template in `sdd-implement` and `sdd-tasks` are owned by P1-08; do not restructure §1, §3 or §4 of `sdd-implement`.
- The `REVIEW.md` template and `/code-review` in `validate-implementation` are owned by P3-11; the `progress.json` harness by P3-10; the review loop plugin by P3-08.
- `plugins/core/skills/parallelize/references/worktrees.md` already documents `remove` and `prune` (`:19-20`); do not edit it.
- No description change in any `SKILL.md` or `agents/*.md`; no new skill, reference or template; no `VERSION` change.

## Acceptance criteria

- [ ] `git diff --stat main` lists exactly four files: `plugins/architect-sdd/skills/sdd-implement/SKILL.md`, `plugins/quality-core/agents/reviewer.md`, `plugins/quality-core/skills/validate-implementation/SKILL.md`, `CHANGELOG.md`.
- [ ] `grep -c '/goal <proof command> exits 0' plugins/architect-sdd/skills/sdd-implement/SKILL.md` → `1`; `grep -c 'Claude-specific' plugins/architect-sdd/skills/sdd-implement/SKILL.md` → `1`; `grep -c 'screenshot or GIF' plugins/architect-sdd/skills/sdd-implement/SKILL.md` → `1`; `grep -c 'xvfb-run' plugins/architect-sdd/skills/sdd-implement/SKILL.md` → `1`.
- [ ] `grep -c 'Run the task.s proof literally' plugins/architect-sdd/skills/sdd-implement/SKILL.md` → `1` (the anchor sentence survives); `grep -c 'recorded and gated\|each proof gated' plugins/architect-sdd/skills/sdd-implement/SKILL.md` → `1`.
- [ ] `grep -c 'git worktree remove --force <tmp> && git worktree prune' plugins/quality-core/agents/reviewer.md plugins/quality-core/skills/validate-implementation/SKILL.md` → `1` for each file; `grep -c 'mktemp -d' ...` → `1` for each file.
- [ ] `grep -rc 'Stop' plugins/core/hooks/hooks.json` → `0`; `git diff --stat main -- plugins/core/hooks plugins/architect-sdd/INDEX.md plugins/quality-core/INDEX.md` → empty.
- [ ] `wc -l plugins/architect-sdd/skills/sdd-implement/SKILL.md plugins/quality-core/agents/reviewer.md plugins/quality-core/skills/validate-implementation/SKILL.md` → `reviewer.md` unchanged in count, the two `SKILL.md` files exactly one line longer than on `main` (`git show main:<path> | wc -l`), each at most 80.
- [ ] `sed -n 25,31p plugins/quality-core/agents/reviewer.md | diff - <(git show main:plugins/quality-core/agents/reviewer.md | sed -n 25,31p)` → no output (report format unchanged); `diff <(sed -n '/^## 5\. Issue the verdict/,$p' plugins/quality-core/skills/validate-implementation/SKILL.md) <(git show main:plugins/quality-core/skills/validate-implementation/SKILL.md | sed -n '/^## 5\. Issue the verdict/,$p')` → no output (verdict block unchanged; anchored on the heading because the one new bullet shifts every line after it).
- [ ] `grep -c '^## \[Unreleased\]' CHANGELOG.md` → `1` and `grep -c 'worktree remove' CHANGELOG.md` → `1`.
- [ ] The cleanup proof from Change step 6: `git worktree list | wc -l` prints the same number before and after; the literal output is in the PR body.
- [ ] `platforms/tools/check.sh` → prints one line starting with `check: OK (`; its six counts must equal the counts of the same command run on a clean export of `main` (`tmp=$(mktemp -d); git archive main | tar -x -C "$tmp"; (cd "$tmp" && platforms/tools/check.sh | grep '^check:')`) because this change adds no plugin, skill, rule, template, index or link; a later `check: claude plugin validate skipped (claude not in PATH)` line is allowed; a `FAIL:` line that names a file outside your diff is reported under Unverified, not fixed. The skill description total (`python3 -c "import re,glob; print(sum(len(re.search(r'^description:\s*(.*)$', open(f).read(), re.M).group(1).strip().strip('\"\'')) for f in glob.glob('plugins/*/skills/*/SKILL.md')))"`) must print the same number as on `main` (6,803 on 2026-10-06; `check_kit.py` never prints it, it only fails above 7,200).
- [ ] `platforms/tools/smoke.sh` → exit 0.
- [ ] `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` → `OK`.
- [ ] `python3 platforms/ci/validations/check_kit.py --links` → a line starting `check: OK (`.

## Conventions

- Everything committed is in English; no layout or path change (the 10.x layout is frozen); `VERSION` untouched.
- `CHANGELOG.md` gets a `## [Unreleased]` entry written with evidence (what, why, proof).
- `INDEX.md` of every touched folder lists every entry by name: nothing is added or renamed here, so both plugin indexes stay unchanged, and the skill descriptions in `plugins/architect-sdd/INDEX.md` and `plugins/quality-core/INDEX.md` must still match the frontmatter verbatim.
- `SKILL.md` at most 80 lines; the agent profile keeps `allowed-tools` lowercase (read, grep, glob, exec) and `tools` as the same Claude names in order (Read, Grep, Glob, Bash).
- `sdd-implement` stays user-only (`triggers: [user]`, `disable-model-invocation: true`); `validate-implementation` keeps `agent: reviewer`, `context: fork`, `background: false`.
- Hooks validator accepts `PreToolUse` (timeout at most 10) and, since P2-07, `PostToolUse` (timeout at most 30): this task adds no hook.
- Backticked paths in skill and agent files are resolved by `check_kit.py` (`platforms/`, `plugins/`, `references/`, `templates/`, `./`, `../` prefixes); the new text cites no such path.
- Conventional Commits with `Refs`: `feat(sdd-implement,reviewer): proof gate per task and worktree cleanup after clean checkout` with `Refs: P3-07` (the kit scopes by skill or component, as in `feat(sdd-tasks): …` and `feat(check_spec): …`).
- PR body = What / Why / How I tested (literal output of the four gates and the cleanup proof) / Refs.
- Gates: `platforms/tools/check.sh`; `platforms/tools/smoke.sh`; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`; `python3 platforms/ci/validations/check_kit.py --links`.

## Report back

Final message, in this order:

1. Done: the four touched paths, each with its final line count; every acceptance command with its literal result (not "passed"); the `git worktree list | wc -l` pair from the cleanup proof.
2. Unverified: anything you could not run (for example `claude plugin validate` when `claude` is not on PATH, which `check.sh` reports as skipped) and the exact `/goal` syntax (code.claude.com/docs/en/goal) and `xvfb-run` syntax if you could not reach the docs.
3. Next step: the PR URL, or the smallest blocker that stops the PR.
4. Proposed CHANGELOG line (one bullet under `### Changed`): `sdd-implement` §2 gates each task on its proof (`/goal <proof command> exits 0` set by the user in Claude Code; the Proof section of the PR body re-run by the reviewer in Devin) and requires a screenshot or GIF for a visual change; `reviewer` and `validate-implementation` now always run `git worktree remove --force` plus `git worktree prune` after the clean checkout, even on failure. Evidence: stratics-docs DPRO-011 records 53 worktrees and 61 branches left behind after batch-20261004-141711; assessment §5 verification row and §6 C3.
