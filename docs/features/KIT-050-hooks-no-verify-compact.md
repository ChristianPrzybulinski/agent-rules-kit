---
id: KIT-050
title: "Guard blocks --no-verify, compaction re-injects git state, AGENTS.md shrinks"
status: done
confirmed: "2026-11-12 (owner's kit review, lane C1; adopt/complement items approved in chat on condition the kit stays as small as possible)"
issue: "#180"
pr: "#182"
---

# KIT-050 — Guard blocks --no-verify, compaction re-injects git state, AGENTS.md shrinks

## Problem and evidence

[FACT] Lane C1 of the owner's 100-repository review (`KIT-REVIEW-2026-11-12/lanes/lane-C1.json`) holds 45 items
for `plugins/core/AGENTS.md`, `plugins/core/hooks/` and `plugins/core/templates/`. Most are covered already
(`KIT-REVIEW-2026-11-12/lanes/ledger-C1.md` gives each one's outcome). Two are not, and a hook can enforce both:

- At `753444c`, `git grep -n no-verify 753444c -- plugins/core` prints nothing. An agent can skip a repository's
  commit and push hooks (gitleaks, a linter) with `--no-verify` or `git commit -n` to get a green commit. This is
  the Never line's "disable a failing test to go green" by another route. A PreToolUse block for it is in rank 004
  affaan-m/ECC (`pre:bash:block-no-verify`), 055 wshobson/agents (`block-no-verify`) and 082 promptfoo/promptfoo.
- After a compaction the agent continues from a summary and `AGENTS.md` § Session asks it to keep the modified files
  in it. Claude Code 2.1.287 sends SessionStart a `source` from `"startup","resume","clear","compact","fork"` (its
  input schema in the installed binary), but the kit's hook matcher is `^startup$`. Rank 056 volcengine/OpenViking
  re-injects state on SessionStart `source` `compact` because PreCompact has no `additionalContext`. `check_kit.py`
  accepts only PreToolUse, PostToolUse and SessionStart hooks, so this is the kit's only route. Rank 065
  mksglu/context-mode bounds the block (about 2 KB), and rank 035 MemPalace/mempalace keeps each hook under 500 ms.

[FACT] `AGENTS.md` was at 59 of 60 lines and repeated itself. "read the repo's `AGENTS.md`" was in Boundaries and again
in Session ("Start: read the repo's `AGENTS.md`; …"). The Craft line "Standards are skills: … Load the one the task
touches; `rules/` loads the Java, Godot and Python sets by file glob." repeated the header ("Procedures, standards
and facts live in skills (loaded by description or by a `rules/` glob)"). Rank 085 EveryInc/compound-engineering-plugin
asks rules to rely on the instructions already in context instead of naming files to read. The Boundaries line keeps
the name once: Claude Code 2.1.287 loads `AGENTS.md` by default only where the project has no `CLAUDE.md` (its
`instructionFiles` text in the installed binary).

## Change

- `plugins/core/hooks/hooks.json` PreToolUse guard: one pattern more, named `git --no-verify`. It blocks
  `--no-verify` on any `git` command and a `-n` short-flag group after `git commit` (`-n`, `-nm`, `-a -n`). Other
  `-n` flags (`git clean -n`, `git log -n 5`, `git push -n`) and `--no-verify` outside `git` stay allowed. A commit
  message that contains `--no-verify`, or a word `-n` after `commit`, is blocked too; the denial asks the user to
  run or confirm it.
- `plugins/core/hooks/hooks.json` SessionStart: matcher `^(startup|compact)$`. On `source` `compact` the hook runs
  `git status --short --branch` and `git rev-parse --short HEAD` in the session's `cwd` (2 s each) and returns
  `additionalContext` "ai-kit: git state after compaction; check the summary against it. <cwd> at <sha>:" followed
  by the status, cut at 2,000 characters with `[truncated]`. Outside a repository it prints nothing. The
  cloud-synced folder warning still runs only at startup.
- `plugins/core/AGENTS.md` (59 → 57 lines):
  - Boundaries Never: "disable or weaken a failing test or check to go green (skip, looser assertion, longer
    timeout, `--no-verify`)" replaces "disable a failing test to go green" (review items from 074 mlflow/mlflow,
    082 promptfoo/promptfoo, 014 addyosmani/agent-skills).
  - Session: "Start: name **the** outcome in one sentence. One session, one outcome; one PR, one concern; a request
    on another topic → say so and offer a follow-up or a new session before starting it." replaces two lines; the
    Boundaries Always line keeps "read the repo's `AGENTS.md`/README before changing".
  - Craft: the "Standards are skills" line is removed.
- `platforms/ci/validations/test_hooks_guard_compact.py`: seven blocked and eight allowed guard commands; the compact
  branch on a temporary repository (branch, short `HEAD`, a modified and an untracked file, no `systemMessage`), its
  2,000-character cut, its silence outside a repository; and each hook (guard, post-edit, startup, compact) under
  0.5 s at the best of three runs.

## Proof

- `python3 -B -m unittest platforms/ci/validations/test_hooks_guard_compact.py`: 6 tests OK. With `hooks.json` from
  `753444c` it fails with 7 failures and 2 errors (all seven blocked commands pass the guard, and the compact
  branch returns no JSON).
- `python3 platforms/ci/validations/check_kit.py --links` runs every guard and SessionStart case against the new
  commands; `bash platforms/tools/smoke.sh`, `CI=1 bash platforms/tools/check.sh`,
  `python3 platforms/tools/gen_index.py --check`, the `platforms/ci/validations` unit tests,
  `platforms/tools/vendor.sh --check`, `claude plugin validate plugins/core` and `gitleaks`.

## History

- 2026-11-12: confirmed (owner's kit review, lane C1) and implemented in #182.
