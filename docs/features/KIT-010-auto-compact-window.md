---
id: KIT-010
title: "doctor caps Claude Code's auto-compact window at 200k"
status: done
confirmed: "2026-10-12 (owner, chat of the Stratics architect session on Claude usage: \"sim, mas consegue ao inves de sugerir, realizar a compactação direto ja\")"
issue: "#88"
pr: "#89"
---

# KIT-010 — doctor caps Claude Code's auto-compact window at 200k

## Problem and evidence

[FACT] On 2026-10-12, a Stratics architect session measured the Claude Code transcripts (`~/.claude/projects/**/*.jsonl`)
since the plan's weekly reset at 2026-10-11T19:00Z. The weekly limit reached 27 % in about 23 hours. Priced at the API
list price only to weigh sessions against each other, 78 % of the weight was cache reads, that is, context size times
turns. The long sessions averaged 350–540k tokens of context per turn, and one reached 958k of its 1M window. Claude
Code compacts a conversation only near its context window, so a 1M-window session re-reads up to 1M tokens on every
tool call.

[FACT] Claude Code 2.1.287 has the user setting `autoCompactWindow` ("Auto-compact window size": `auto`, or 100k–1M
tokens such as `200k` or `200000`), and the environment variable `CLAUDE_CODE_AUTO_COMPACT_WINDOW` takes precedence over
it. A `PreCompact` hook can only block a compaction, never start one, so the setting is the way to compact
automatically. A running session keeps the window it started with; the setting applies to sessions opened afterwards.

[HYPOTHESIS] The plan's limit weighs cache reads as the API list price does; if it weighs them less, the saving is
smaller than the share above.

## Change

- `platforms/tools/doctor.sh` § 6 (Claude) gains `ensure_claude_auto_compact`:
  - when `~/.claude/settings.json` has no `autoCompactWindow`, it writes `"200k"` and keeps every other key
    (`fix: claude autoCompactWindow set to 200k in <path> (KIT-010)`);
  - an explicit value at or below 200k is `ok`;
  - a value above 200k, or `auto`, is kept and reported as `warn`, because it is the owner's choice;
  - a set `CLAUDE_CODE_AUTO_COMPACT_WINDOW` is reported as `warn`, because it overrides the file;
  - an unreadable `settings.json` is a `FAIL`, and the file is not rewritten.
- `platforms/tools/smoke.sh`: the stub-Claude doctor runs check the `fix` on the first run, the `ok` on the second, and
  that a `500k` set by the owner is kept with its `warn`.

## Proof

`bash platforms/tools/check.sh`; `bash platforms/tools/smoke.sh`; `python3 platforms/ci/validations/check_kit.py --links`.

## History

- 2026-10-12: confirmed (owner, chat of the Stratics architect session on Claude usage) and implemented.
