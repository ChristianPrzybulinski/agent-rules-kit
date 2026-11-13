---
id: KIT-058
title: "The plugin hooks change after the owner's hook-by-hook review"
status: done
confirmed: "2026-11-12 (owner, chat of the kit always-on review session: \"Yes, keep it\" for the guard, \"Change the message\" for its git branch -D reason, \"Sim, só registrar\" (yes, just record it) for the guard on Codex, \"e concordo, tirar o ramo do java\" (I agree, remove the Java branch) for the lint hook, \"Sim, as duas\" (yes, both) for the SessionStart hook)"
issue: "#206"
pr: "#208"
---

# KIT-058 — The plugin hooks change after the owner's hook-by-hook review

## Problem and evidence

[FACT] On 2026-11-12, after KIT-057, the owner reviewed the three hooks of `plugins/guardrails/hooks/hooks.json` one at a
time, in the same format: what each does, an example, its origin, who enforces it, the risk without it, and a
recommendation set against its 2 strongest alternatives.

### Guard (PreToolUse): kept, git branch -D reason extended

[FACT] Claude Code transcripts under `~/.claude/projects` from 2026-10-05 to 2026-11-12 hold 367 guard denies in 250
sessions: `rm -rf` 214, `git branch -D` 58, `git checkout --` 47, `git push --force` 11, the rest 37. Of the 214
`rm -rf` denies, 144 remove a path held in a variable (`rm -rf $S`), which a regex hook cannot expand, and 19 a literal
`/tmp` path, so allowing literal temporary paths would remove 19 denies and add a bypass to test. Denies that caught real
damage include `rm -rf /var/lib/vz/haos-18.4` on a Proxmox host and `git checkout -- platform/review-loop/loop.py` over
uncommitted edits. The owner kept the guard as it is.

[FACT] The owner then asked whether the guard gets in the way of removing a worktree. `git worktree remove`, with or
without `--force`, and `git worktree prune` pass; `rm -rf` of a worktree folder is denied, and no transcript deny had
one as its target. The friction is the branch: 45 of the 58 `git branch -D` denies ran in the same command as
`git worktree remove` (`git worktree remove ../wt-x && git branch -D feat/x`), none of the 58 had the bare
`git branch -D <one name>` form that KIT-020's merged-PR exception accepts, and across all transcripts one bare
`git branch -D` passed. The exception works when reached: on the KIT-057 worktree, `git branch -D kit/always-on-review`
alone passed (tip `8367399`, the head of merged PR #203) and `git branch -D main` was denied. Accepting
`git branch -D` inside a chained command would need more parsing in the inline hook and opens
`cd other-repo && git branch -D x`, where the hook would read the branch of the wrong repository; the owner chose the
message.

### Guard on Codex: gap recorded, no hook installed

[FACT] Codex 0.164.0 runs hooks from `~/.codex/hooks.json`, `~/.codex/config.toml`, a trusted project's `.codex/` and a
plugin's `hooks/hooks.json`, and runs a non-managed hook only after the user trusts it in `/hooks`, again after each
change to it (OpenAI Codex hooks documentation, read 2026-11-12). The installed `guardrails` plugin carries
`hooks/hooks.json` in `~/.codex/plugins/cache/ai-kit/guardrails/12.0.0/`, `~/.codex/config.toml` holds no hook, and none
of the 318 local Codex rollouts (2026-11-04 to 2026-11-12) holds a hook-made message or an `ai-kit guard:` reason.
Replaying their 18,202 shell commands (the `cmd` of each `tools.exec_command` call) through the guard denies 8, all
`git restore` of paths inside the session's own worktree (2026-11-05 and 2026-11-07); none is `rm -rf`,
`git branch -D` or `git reset --hard`. A user-level hook installed by `doctor.sh` would need the owner to trust it after
every guard change and would stop unattended loop workers on those restores; Codex `prefix_rule` rules match only the
start of a command. The owner chose to record the gap. It is wrong if a Codex session loses work to a command the guard
denies, or Codex starts running `rm -rf`, `git reset --hard` or `git branch -D`.

### Lint after edit (PostToolUse): Java branch removed

[FACT] The PostToolUse hook runs `gdformat` and `gdlint` on `*.gd`, `google-java-format --replace` on `*.java` and the
synced `check_spec.py` on `docs/spec/**/*.md`; a missing tool prints a notice and exits 0, findings exit 2. Claude Code
transcripts hold 177 Java notices ("google-java-format not available") in 18 sessions from 2026-10-08 to 2026-11-09 and
no Java run. 140 of them fell in the week of 2026-10-05; the last three weeks hold 37 in 7 sessions, as Java work moved
to Codex, which runs no plugin hook. Java formatting is already checked by `spotless:check` in the Stratics server
build, which pins google-java-format 1.30.0 (`server/pom.xml`, spotless-maven-plugin 3.10.2); it failed on format 6
times in 5 Claude Code sessions from 2026-10-04 to 2026-11-06, each fixed by `spotless:apply`. Installing the formatter
on the host would add a dependency and a second version to keep equal to the POM's (the Homebrew formula is 2.0.0).
The `gdlint` branch reported 12 findings (2 in project files, 10 in scratch files) and the spec branch 17 (2026-10-06 to
2026-10-12); both stay, and the Stratics CI checks both again. The owner chose to remove the Java branch. It is wrong if
`spotless:check` format failures in Claude Code sessions pass about one a week, or Claude Code becomes the main Java
implementer again; the hook would then run the formatter at the version the project's POM pins.

### Session start (SessionStart): warning for repositories only, edited repositories after compaction

[FACT] The SessionStart hook has two branches. On `startup` it warns when the working directory sits in an iCloud,
File Provider, Dropbox or OneDrive folder (KIT-021, after the 2026-10-30 iCloud incident in which a folder rename was
blocked for 3 h 13 min). Claude Code transcripts hold 2 such warnings, both on 2026-11-02 and both for
`~/Documents/Finance`, which is not a Git repository; the message says the sync client indexes `.git`, so both were
false alarms. On `compact` it adds `git status --short --branch` and the short `HEAD` of the working directory
(KIT-050): 73 injections in 22 sessions from 2026-11-12 to 2026-11-13 (UTC). 48 of them followed an Edit, Write or
NotebookEdit call in the same transcript, and 26 of those, in 5 sessions, showed a checkout other than the repository
of the last edited file, because the payload's `cwd` follows the shell's last `cd`; in this session one showed
`stratics-docs-loop` behind `origin/main` by 33 commits while the work was in `wt-kit-always-on`. Claude Code passes
`transcript_path` to every hook (Claude Code hooks reference, read 2026-11-12); run on this session's 42 MB transcript with
the parent folder `~/Developer/GitHub` as `cwd`, the new hook reported `wt-kit-always-on` and its status in 65 ms. The owner approved both
changes. They are wrong if a repository in a synced folder starts a session without a warning, or the added
repositories are mostly ones the session had finished with; the compact branch would then go back to the working
directory alone.

## Change

`plugins/guardrails/hooks/hooks.json`, PreToolUse guard: when `git branch -D` is the only match, the deny reason ends
with "The branch of a merged PR passes when `git branch -D <branch>` runs as its own command." Every other reason is
unchanged. `platforms/ci/validations/test_hooks_guard_merged_branch.py` checks the hint on a chained and a bare
`git branch -D`, and its absence when `rm -rf` or `git reset --hard` is denied; on the guard of `origin/main` the new
test fails on both hinted commands. `docs/design.md` names the hint beside the KIT-020 exception. `docs/design.md` adds Codex sessions, with the replay's numbers, to what the guard does not cover; the README platform table already says Codex has no hooks.

`plugins/guardrails/hooks/hooks.json`, PostToolUse lint hook: the `.java` branch is removed, so a Java edit runs nothing and prints nothing. `platforms/ci/validations/hook_post_edit_cases.json` replaces its three Java cases with two that expect exit 0 and no output, with and without a failing `google-java-format` on `PATH`. `docs/design.md` leaves Java formatting to the project's `spotless:check`.

`plugins/guardrails/hooks/hooks.json`, SessionStart hook: on `startup` it first finds the root of the working directory's repository, the nearest folder with a `.git` entry (a worktree's `.git` file counts), exits 0 in silence when there is none, and warns only when that root sits inside a synced folder; the message is unchanged. On `compact` it reads the last 4 MB of the payload's `transcript_path`, takes the `file_path` or `notebook_path` of the Edit, Write, MultiEdit and NotebookEdit calls from the newest back, and adds the state of up to two repositories other than the working directory's as `<root> at <sha> (edited in this session):` with the same 2000-character cut. Every Git call shares a 4 s budget inside the 5 s timeout, and a missing or unreadable transcript leaves the working directory alone; a working directory outside Git no longer silences the edited repositories. `platforms/ci/validations/hook_session_start_cases.json` gives every repository case a `.git` entry and adds four cases; two of them, a non-repository and a repository root above the synced folder, fail on the previous hook. `platforms/ci/validations/test_hooks_guard_compact.py` adds three tests, two of which fail on the previous hook, and a 6 MB transcript to the latency budget; `platforms/ci/validations/test_sync_project.py` gives its two targets a `.git` folder. The README platform table, `docs/design.md` and `CONTRIBUTING.md` name the Git state after compaction.

## Proof

`bash platforms/tools/check.sh`, `CI=1 bash platforms/tools/check.sh`, `bash platforms/tools/smoke.sh`,
`python3 platforms/ci/validations/check_kit.py --links`, `python3 platforms/tools/gen_index.py --check`,
`python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` and
`gitleaks git --redact --log-opts=origin/main..HEAD`; results in the PR body.

## History

- 2026-11-12: confirmed (owner, chat, hook by hook).
- 2026-11-12: done (PR #208).
