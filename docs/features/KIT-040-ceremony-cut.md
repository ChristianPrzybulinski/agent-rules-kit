---
id: KIT-040
title: "Feature records only for big kit changes, generated plugin indexes and no docs/plans"
status: done
confirmed: "2026-11-11 (owner, chat of the kit review session: phase 4 of the approved plan)"
issue: "#150"
pr: "#152"
---

# KIT-040 — Feature records only for big kit changes, generated plugin indexes and no docs/plans

## Problem and evidence

[FACT] A kit change pays a fixed ceremony before its content counts. On `origin/main` at `1edc0ab`, the 32 commits
since 2026-10-15 changed 7,941 lines (added plus deleted, from `git log --numstat`): `docs/features/` and
`CHANGELOG.md` took 2,174 (27.4%), `INDEX.md` files and `plugin.json` or `marketplace.json` manifests 498 (6.3%), and
skills, rules, agents and `AGENTS.md` 169 (2.1%). KIT-032, a rule and skill sharpening, touched 51 files
(`git show --stat 7ea3a26`). Before this change every kit change needed a `docs/features/KIT-NNN` record and a
`kit-feature` issue (`docs/maintenance.md`, "kit feature" row), and every skill, rule, template, agent or eval edit
needed a hand edit of the plugin's `INDEX.md`, whose skill descriptions copied each `SKILL.md` frontmatter.

[FACT] `docs/plans/` held 38 files of the 2026-10 kit assessment (three READMEs, `assessment.md` and 34 prompts), all
executed; the work they describe lives in `CHANGELOG.md`, `docs/features/` and git history.

[FACT] `plugins/core/hooks/hooks.json` holds three inline `python3 -c '…'` commands (PreToolUse guard, PostToolUse
format and lint, SessionStart synced-folder warning).

## Change

1. **Records only for big changes.** `docs/maintenance.md` ("kit feature" row), the Process section of
   `docs/features/README.md`, `docs/INDEX.md` and `.github/PULL_REQUEST_TEMPLATE.md` say: a `docs/features/KIT-NNN`
   record and a `kit-feature` issue are for a hook, `plugins/core/AGENTS.md`, plugin structure or manifests, a check,
   gate or script behavior change, or a new or removed skill. Any other change (a skill, rule, reference, template or
   doc text edit) needs only its `CHANGELOG.md` line, and the PR body carries the why. Records written before KIT-040
   stay.
2. **Generated plugin indexes.** `platforms/tools/gen_index.py` writes each `plugins/*/INDEX.md` from the plugin: the
   H1 and `Depends on` line from `.claude-plugin/plugin.json`, one row per skill from the `SKILL.md` frontmatter (name,
   `description`, invoked by user or by user and model), and one bullet per entry of `AGENTS.md`, `rules/`, `agents/`,
   `templates/`, `evals/` and `hooks/`. It iterates `plugins/*`, so a new plugin needs no registration, and reads the
   frontmatter with its own parser so PyYAML changes nothing. `check.sh` runs `gen_index.py --check` after
   `check_kit.py`; a stale index fails with the path and `python3 platforms/tools/gen_index.py`. `check_kit.py`
   section 9 now requires only that each plugin has an `INDEX.md` and keeps its eval-case checks. The root
   `INDEX.md`, `docs/INDEX.md` and `platforms/**/INDEX.md` stay hand-written. All 14 `plugins/*/INDEX.md` are
   regenerated. `test_gen_index.py` (9 tests, on a throwaway kit) covers skill rows, invocation, `|` escaping, every
   listed directory, a manifest-only plugin, `--check` on a missing, hand-edited, changed and new plugin, idempotence
   and unreadable files.
3. **`docs/plans/` deleted.** The directory and its row in `docs/INDEX.md` go, and `docs/features/README.md` no longer
   links to it. Two dated sentences in `KIT-024` and `KIT-025` still name files that lived there; they are history.
4. **Hooks stay inline.** The three commands are not moved to script files. A script needs a path to itself:
   Claude Code 2.1.287 exports `CLAUDE_PLUGIN_ROOT` to a plugin hook (checked with a throwaway plugin whose
   `SessionStart` hook wrote its environment), but Devin 3000.12.43 was not checked: its binary holds the
   `CLAUDE_PLUGIN_ROOT` and `PLUGIN_ROOT` strings beside the hook code, and installing a throwaway plugin to read the
   hook environment was refused by the permission classifier, so no run exists. A hook script that is not found exits
   with a code other than 2, and only 2 blocks, so the PreToolUse guard would fail open in a host that does not set the
   variable. The 25 hook cases run each command with `bash -c` and cannot prove a host's locator, so the brief's rule
   applies: leave the commands inline. `docs/design.md` § "One hook file" records this.

## Proof

- `bash platforms/tools/check.sh` and `CI=1 bash platforms/tools/check.sh`: exit 0, "check: OK (14 plugins, 46 skills,
  3 rules, 13 templates, 21 indexes, 96 links, 25 hook cases)", "gen_index: plugin indexes are current", and
  `claude plugin validate` passed for each plugin and the marketplace.
- `bash platforms/tools/smoke.sh`: exit 0, "smoke: OK (46 skills, app fallback, cleanup, symlink safety, manifests,
  sync-project, rules copy, vendored skills, multi-profile sync, no-spec repo)".
- `python3 platforms/ci/validations/check_kit.py --links`: exit 0, the same "check: OK" line.
- `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`: exit 0, "Ran 103 tests", "OK
  (skipped=1)" (94 before, plus the 9 of `test_gen_index.py`).
- `test_gen_index.py` fails on two mutants of `gen_index.py`: dropping the `|` escape, and treating any existing index
  as current.
  `gen_index.py --check` exits 1 and names `plugins/<name>/INDEX.md` and the regenerate command for a missing, a
  hand-edited and a stale index.
- `gitleaks git --redact --log-opts="origin/main..HEAD"`: exit 0, "no leaks found".
- Hooks: no hook command changed, so the 25 hook cases still run the same strings. A throwaway plugin with a
  `SessionStart` hook run by `claude -p --plugin-dir` (2.1.287) printed `CLAUDE_PLUGIN_ROOT=<plugin dir>`,
  `CLAUDE_PLUGIN_DATA` and `CLAUDE_PROJECT_DIR`.
- Not verified: the hook environment in Devin 3000.12.43 (no run, see Change 4); the generated indexes were not read by
  Devin or Codex, which see the same files as before apart from the INDEX content.

## History

- 2026-11-11: confirmed (owner, chat of the kit review session, phase 4 of the approved plan); issue #150.
- 2026-11-11: done in #152. The brief's fourth item (hook commands into script files) was left out, see Change 4.
