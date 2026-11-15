---
id: KIT-071
title: "Claude Code and Codex load the cross-cutting skills at their events, by trigger lines, hooks, preload and a rule, and the kit measures it"
status: confirmed
confirmed: "2026-11-14 (owner, chat of the KIT-067 design session: the skill-usage plan, relayed to the implementing session as items 1-7)"
issue: "#233"
pr: "#235"
---

# KIT-071 — Claude Code and Codex load the cross-cutting skills at their events, by trigger lines, hooks, preload and a rule, and the kit measures it

## Problem and evidence

[FACT] A skill loads when the model judges its description relevant to the prompt (Claude Code skills doc), and on the
owner's machine Claude Code rarely makes that call. Over the 60 days to 2026-11-14 of local transcripts, measured by the
design session's scripts: Claude Code loaded `git` in 0 sessions, `docker` in 0, `parallelize` in 0, `session` in 3,
`investigate` in 0, `review` in 2 and `security` in 0; Codex loaded them in 0, 1, 11, 108 of 117, 5, 5 and 2. Codex
loop children never commit (a consumer project's rule), so its `git` 0 is expected.

[FACT] In 28 of 28 Claude desktop sessions that edited `.gd` or `.java`, the transcript carries the skill listing
with the coding skills and their descriptions, and none was invoked. A minimal `claude -p` repro with
`claude-haiku-4-5`: a skill whose description says "Use when editing *.zz files" was listed and not invoked (3/3);
a skill with `paths` was listed only after a matching Read and its content never loaded (2/2); a path rule was
injected after the Read (attachment `nested_memory`, 1/1).

[FACT] `platforms/tools/skill_usage.py --days 60` on 2026-11-14, this branch: Claude Code 1,496 sessions, Codex 118;
`git` 1 and 0, `parallelize` 1 and 11, `session` 10 and 109, `investigate` 1 and 5, `review` 3 and 5, `security` 0
and 2, `docker` 0 and 1. The Claude counts include the sessions of 2026-11-14 that read `SKILL.md` files while
designing and building this change (the tool counts a Read of `SKILL.md` as a load).

[FACT] Official docs read on 2026-11-14 against Claude Code 2.1.287 (`claude --version`):
- settings reference (code.claude.com/docs/en/settings-reference): `includeGitInstructions`, boolean, default
  `true`, any settings file; `false` leaves out the built-in commit and PR instructions and the git status snapshot;
  `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS=1` (env-vars page) takes precedence;
- hooks (code.claude.com/docs/en/hooks): PreToolUse `hookSpecificOutput` takes `additionalContext`, placed "next to
  the tool result", so it reaches the model after the command ran; SessionStart `additionalContext` is injected before
  the first prompt; matcher sources `startup`, `resume`, `clear`, `compact`, `fork`; a handler-level `if` filter
  exists for tool events;
- sub-agents (code.claude.com/docs/en/sub-agents): `skills` lists skills whose full content is injected at the
  subagent's start; plugin subagents ignore only `hooks`, `mcpServers` and `permissionMode`;
- plugin evals (code.claude.com/docs/en/plugin-evals): a run loads only the plugin under test, with its skills, hooks
  and agents, and "Nothing personal or project-level loads", no `CLAUDE.md` included; `append_system_prompt` appends
  text to the run's system prompt; `tool_used` with `tool: Skill` is the skill-trigger grader.

## Change

1. `plugins/guardrails/AGENTS.md` (60 of 60 lines): each cross-cutting skill gets the event that loads it at the head
   of the line that already owned its topic, plus one new line for `git`:
   - "Before a handoff or closeout → load skill `session`." (§ Session, was "Detail: skill `session`.")
   - "Independent steps or long commands → load skill `parallelize`." (§ Work loop, was "Detail: skill `parallelize`.")
   - "Before a commit, PR or release → load skill `git`." (§ Work loop, new line)
   - "A bug with no named cause → load skill `investigate` before any fix." (§ Work loop)
   - "A trust-boundary change, a secret or a dependency CVE → load skill `security`." (§ Security, was "Detail: skill `security`.")
   - "\"Is it done?\", or about to claim done or open a PR → load skill `review`." (§ Truth)
   `sdd-intake` gets its line once KIT-066 (#232) merges: the skill does not exist on `main` yet.
2. `platforms/tools/sync-project.sh` writes `"includeGitInstructions": false` into the generated
   `.claude/settings.json`, and `--check` reports "includeGitInstructions: want false" when it is missing or `true`
   (`test_sync_project.py` covers both). README § Claude Code tells the user to set it in `~/.claude/settings.json`
   or export `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS=1`; bootstrap and doctor never write it there.
3. `plugins/guardrails/hooks/hooks.json` SessionStart, a second group (matcher `^(startup|clear)$`) that prints a fixed
   `additionalContext`: name the one outcome; read the repository `AGENTS.md` and README; verify the working directory,
   Git root, branch and head commit with the three `git` commands; skill `session` holds the steps. No interpreter
   starts: it is one `printf`.
4. `hooks.json` PreToolUse, a second group (matcher `^(exec|Bash)$`, timeout 5 s) that never denies: after a
   `git commit` it adds the `git` § 3-4 essentials for the next step (title, explicit staging, body with why, what and
   proof, fix the unpushed commit, `git fetch` and `git log --oneline origin/main..HEAD` before a push, no force-push
   without the user), and after `gh pr create` the § 7 essentials (body contents, `gh pr edit`, then
   `gh pr checks <n> --watch` and each check reported by name). The text is written for the step after the command,
   because the context arrives with the tool result. The command is matched at a command start, after `cd ... &&`,
   variable assignments, `env`/`sudo` and git's `-C`/`-c`/`--` options; `echo git commit`, `git commit-tree` and
   `gh pr list` stay silent. `check_kit.py` runs it on `hook_git_context_cases.json` (7 commit, 5 PR, 8 silent), runs
   the checklist apart from the synced-folder cases, and fails when either hook is missing; `test_hooks_context.py`
   covers malformed input, the 0.5 s budget and two broken copies that `check_kit.py` must fail.
5. `plugins/guardrails/agents/reviewer.md`: `skills: [review, testing]`; `agent.schema.json` accepts `skills` and
   `check_kit.py` fails on a name that is not a kit skill. Bare names resolve inside the plugin: with
   `claude -p --setting-sources project --plugin-dir plugins/guardrails --model haiku`, a `guardrails:reviewer` asked
   for the level-1 headings of the skills injected at its start answered `# Review` and `# Testing`; the same run with
   `origin/main`'s `reviewer.md` answered `NONE` (one run each).
6. New rule `plugins/guardrails/rules/docker.md` (Compose files, `Dockerfile*`, `.env.example`; 10 bullets): no
   `docker compose down -v`, `docker volume rm` or prune by an agent; no secret in Compose, a Dockerfile or
   `.env.example`; a top-level `name:`; a healthcheck per long-running service with `service_healthy`; pinned tags;
   `127.0.0.1:` ports; named data volumes; staged, non-root images with `.dockerignore`; every variable in
   `.env.example`; `docker compose config --quiet` after an edit. Skill `docker` keeps the procedures and running or
   remote hosts. `sync-profiles.txt` sends it to `godot java python docs`: like `json.md`, the `docs` profile keeps
   its globs repository-wide, so a monorepo's root `compose.yml` matches (`test_sync_project.py` checks it).
7. Measurement:
   - six eval cases tagged `trigger` (`git-trigger-commit-this`, `session-trigger-handoff`,
     `parallelize-trigger-three-checks`, `investigate-trigger-slow-job`, `security-trigger-download-endpoint`,
     `review-trigger-can-i-merge`), plain requests that never name the skill, each with one `tool_used: Skill`
     grader. The three repository cases scaffold a git fixture. A run loads no `CLAUDE.md`, so each case repeats its
     skill's `AGENTS.md` trigger bullet in `append_system_prompt`, and `check_kit.py` fails when the two differ
     (checked by editing one case: it failed, and passed once restored). Alone, the line is more salient than among
     the 60 lines of a real session [HYPOTHESIS], so these cases overstate the trigger line's effect.
   - `platforms/tools/skill_usage.py`, from the design session's three scripts: per kit skill (`--all`, `--skill`),
     the Claude Code sessions that called it with the Skill tool, read its `SKILL.md` or typed its command (a
     subagent transcript counts for its session), and the Codex rollouts whose tool calls name its `SKILL.md`;
     `--days` (30), a table or `--json`. `test_skill_usage.py` covers what counts and what does not on synthetic logs.

Not changed: Codex runs no plugin hook and no subagent preload, so for Codex only items 1 and 6 apply (item 6 through
the `AGENTS.md` Boundaries line that sends every agent to the matching `.claude/rules/*.md`).

## Proof

Trigger evals, 2026-11-14, Claude Code 2.1.287, `claude plugin eval plugins --tag trigger --runs 5 --ablation none
--no-publish --trust-plugin --scaffold --model claude-sonnet-5-5 -j 4 --threshold 0.8`; score = share of runs whose
`skill-fired` grader passed:

| case | this branch | `origin/main` `3807c85` plugin, same cases without the trigger line |
|---|---|---|
| `git-trigger-commit-this` | 1.00 | 1.00 |
| `session-trigger-handoff` | 1.00 | 1.00 |
| `investigate-trigger-slow-job` | 1.00 | 1.00 |
| `security-trigger-download-endpoint` | 1.00 | 0.00 |
| `review-trigger-can-i-merge` | 1.00 | 1.00 |
| `parallelize-trigger-three-checks` | 0.00 | 0.00 |
| overall, cases ≥ 0.8, cost | 0.83, 5 of 6, $2.06 | 0.67, 4 of 6, $2.02 |

- [FACT] No run was granted Bash: with `--allow-tools Bash` every run stopped before the model with "the Docker
  (~/.docker, DOCKER_CONFIG) credential store on this machine holds a symbolic link inside it" (21 links, Docker
  Desktop's `~/.docker/bin`), score 0 and $0.00. So the three repository cases could read their fixture but not run
  `git` or the scripts, which leaves the Skill call as the one useful action. With the sandbox loading only the 26 kit
  skills and no `CLAUDE.md` or other context, these scores are an upper bound on a desktop session [HYPOTHESIS]; the
  60-day counts above are the real-session baseline.
- [FACT] The ≥ 0.8 target holds for 5 of 6 skills and fails for `parallelize`. In two kept traces Claude ran the three
  checks concurrently on its own (one shell call with background jobs and `wait`, delegated to a subagent) without
  loading the skill. One more concrete trigger line ("Two or more independent commands, reads or checks, or one that
  runs for minutes → load skill `parallelize` before starting them.") scored 0.20 over 5 runs ($0.39) and was
  reverted. Whether `parallelize` should stay a skill belongs to its planned slimming, not to more wording here.
- [FACT] The trigger line moved `security` from 0.00 to 1.00; the other four already loaded in this sandbox from
  their descriptions alone.
- [FACT] In one kept `parallelize` trace the first tool call was
  `git rev-parse --show-toplevel; git branch --show-current; git rev-parse HEAD`, the SessionStart checklist's three
  commands, which `origin/main` does not inject.
- Falsifier for the real-session effect: after 30 days with this change installed, `skill_usage.py --days 30` still
  shows Claude Code loading `git` in about 0 sessions.

Gates at `7f95c0a` (2026-11-14, macOS, load average 14 to 17 from other sessions):

| command | result |
|---|---|
| `bash platforms/tools/check.sh` | exit 0: `check: OK (1 plugins, 26 skills, 6 rules, 11 templates, 14 readmes, 111 links, 49 hook cases, 14 shell scripts)`, `gen_index: plugin indexes are current`, both `claude plugin validate` passed (`origin/main`: 5 rules, 110 links, 28 hook cases, 11 shell scripts) |
| `CI=1 bash platforms/tools/check.sh` | exit 0, same lines |
| `python3 platforms/ci/validations/check_kit.py --links` | exit 0, same `check: OK` line |
| `bash platforms/tools/smoke.sh` | exit 0: `smoke: OK (26 skills, app fallback, cleanup, symlink safety, manifests, sync-project, rules copy, vendored skills, multi-profile sync, no-spec repo)` |
| `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` | `Ran 253 tests in 489.814s`, `FAILED (failures=1, skipped=5)`: `test_each_hook_within_budget (hook='compact-transcript')` `0.705 s` against 0.5 s. That hook is `SessionStart[0]`, unchanged. Rerun of the test alone: this branch `0.506 s` FAILED then OK; `origin/main` `3807c85` `0.523 s` FAILED then OK, so it is pre-existing and load-bound. The new suites pass: `test_hooks_context.py` 8, `test_skill_usage.py` 6, `test_sync_project.py` 28 |
| `gitleaks git --redact --log-opts="origin/main..HEAD"` | gitleaks 8.30.1, `no leaks found` |


## History

- 2026-11-14: confirmed (owner, KIT-067 design session); implemented on branch `kit-071-skill-use`.
