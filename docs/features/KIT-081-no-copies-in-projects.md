---
id: KIT-081
title: "The kit copies nothing into a project: skills and CI run the kit's own files"
status: confirmed
confirmed: "2026-11-16 (owner, chat of the agent-rules-kit 13.1.0 bundle session, after the platforms/ review: 'Sim, registre')"
issue: "#N"
pr: ""
---

# KIT-081 — The kit copies nothing into a project

## Problem and evidence

The owner's principle, in the platforms/ review: a plugin should hold its files and run them against the project that
uses it, not install copies into that project.

[FACT] Stratics `main` (`git ls-tree -r origin/main`, 2026-11-16) holds 188 files that `platforms/tools/sync-project.sh`
wrote:

| Group | Files | Why it is there today |
|---|---|---|
| `.claude/skills/` and `.claude/ai-kit/` (the pin) | 119 + 35 | KIT-072: Claude Code registers one `ai-kit` marketplace ref per user, and on 2026-11-15 every kit merge changed what each Stratics session loaded, because `refresh.sh` followed `main` |
| `.github/spec-lint/` | 16 | The project's GitHub CI runs on a machine without the kit |
| `.claude/rules/guardrails-*.md` (and the `AGENTS.md` blocks) | 11 | Path rules: Claude Code loads a rule by path from the project's `.claude/rules/`; Codex reads only `AGENTS.md` |
| `kit*.just`, `.github/merge-drivers/` | 4 + 1 | `fmt`/`lint`/`test`/`verify` commands and the keyed-CSV merge driver |
| `.claude/settings.json`, `CLAUDE.md` | 2 | Turn the plugin on for the project; `CLAUDE.md` imports `AGENTS.md` |

[FACT] Each kit release needs a project PR that rewrites those copies (#299: the Stratics re-pin after 13.1.0).
`sync-project.sh` is 1,056 lines and its helpers `sync_pinned_plugin.py`, `sync_agents_md.py` and `sync_just.py` another
1,027 (`wc -l`), and 8 test modules name `.github/spec-lint/` alone (`git grep -l spec-lint -- platforms/ci/validations/test_*.py`).

[FACT] What changed since KIT-072: from 13.1.0 (#271) the user install follows the newest `vX.Y.Z` release tag, not
`main`, so the installed plugin changes only when a release is published. The kit repository is public
(`gh repo view --json visibility`), so a project's CI can fetch it at a tag without a token.

## Change

The project keeps configuration only: `.claude/settings.json` (the plugin is on), `CLAUDE.md`, and the CI lines that
name the kit release. Every check runs from the kit's own files. Three stages, one PR each, every stage with its
migration line for consumer projects:

1. **Spec tools from the kit.** Skills, the post-edit hook and the `docs` just module call
   `~/.ai-kit/platforms/ci/validations/` (`check_spec.py`, `row_checks.py`, `spec_trace.py`,
   `check_docs_structure.py`) with `~/.ai-kit/platforms/ci/schemas/`, not `.github/spec-lint/`. The project's CI gets the
   same path by fetching the kit at a release tag (the `spec-lint.yml` and `pr-contract.yml` templates, or a reusable
   workflow the project calls with `@vX.Y.Z`), so a command reads the same locally and in CI. `sync-project.sh` stops
   writing `.github/spec-lint/`, and `--check` stops comparing it.
2. **No pin.** The vendored mode (`--vendor-skills`, `.claude/skills/` copies, `.claude/ai-kit/`,
   `guardrails-pinned`) goes; the project turns on `guardrails@ai-kit`, which follows the release the machine installed.
3. **Path rules without copies.** A plugin hook gives the agent the rule when it reads or edits a file the rule's globs
   match, as the `git` hook already adds context to a commit; `.claude/rules/` copies and the `AGENTS.md` blocks go once
   it is measured.

The starter files a new project needs (`.gitignore`, `.gdlintrc`, the PR template) are the project's own: a skill writes
them once from the kit templates when it sets the project up; no sync script copies them.

Open before stage 2 and 3 (each `[HYPOTHESIS]` until checked against the installed version or its docs):

- A Claude Code plugin cannot ship path-scoped rules (stage 3 rests on it).
- Codex has no way to receive a path rule without a file in the project (stage 3 keeps the `AGENTS.md` block for Codex
  if so).
- No consumer needs a kit version other than the machine's for longer than a release cycle (stage 2 rests on it).

What proves the change wrong: a consumer that must stay on an older kit release while the machine moves on, or a
hook-delivered rule followed less often than the path rule (measured as in KIT-070).

## Proof

Per stage: `bash platforms/tools/check.sh`, `python3 platforms/tools/run_tests.py --start platforms/ci/validations
--changed-from origin/main`, the consumer fixture (`test_consumer_fixture.py` in `ci-full.yml`) passing with no
`.github/spec-lint/` in the project, and `git grep -n 'spec-lint/' -- plugins platforms/kits` printing nothing after
stage 1.

## History

- 2026-11-16: confirmed (owner). Replaces the unrecorded starter-file proposal of the same session (a sync step that
  wrote starter files into a project).
