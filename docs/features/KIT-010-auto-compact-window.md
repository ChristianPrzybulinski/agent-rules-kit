---
id: KIT-010
title: "doctor caps Claude Code's auto-compact window at 300000 tokens"
status: done
confirmed: "2026-10-12 (owner, chat of the Stratics architect session on Claude usage: \"sim, mas consegue ao inves de sugerir, realizar a compactação direto ja\"); 300000 on 2026-11-12 (owner, chat: \"Sim, 300k\")"
issue: "#88"
pr: "#89"
---

# KIT-010 — doctor caps Claude Code's auto-compact window at 300000 tokens

## Problem and evidence

[FACT] On 2026-10-12, a Stratics architect session measured the Claude Code transcripts (`~/.claude/projects/**/*.jsonl`)
since the plan's weekly reset at 2026-10-11T19:00Z. The weekly limit reached 27 % in about 23 hours. Priced at the API
list price only to weigh sessions against each other, 78 % of the weight was cache reads, that is, context size times
turns. The long sessions averaged 350–540k tokens of context per turn, and one reached 958k of its 1M window. Claude
Code compacts a conversation only near its context window, so a 1M-window session re-reads up to 1M tokens on every
tool call.

[FACT] Claude Code 2.1.287 has the user setting `autoCompactWindow` ("Auto-compact window size"), and the environment
variable `CLAUDE_CODE_AUTO_COMPACT_WINDOW` takes precedence over it. A `PreCompact` hook can only block a compaction,
never start one, so the setting is the way to compact automatically. A running session keeps the window it started
with; the setting applies to sessions opened afterwards.

[FACT] In `settings.json` the value must be a number. The installed 2.1.287 binary declares the setting as
`C().int().min(eWe).max(CZe).optional().catch(void 0)` with `eWe=1e5,CZe=1e6`: an integer from 100000 to 1000000, and
any other value is dropped without a message, so the model's default window applies. The shorthand `auto`, `200k`,
`500k` or `200` is parsed only by the `--autocompact` flag and the `/autocompact` command. The `"200k"` this doctor
wrote from 2026-10-12 was therefore never applied; the owner saw it ignored on 2026-10-13.

On 2026-11-12 the owner raised the window from 200k to 300000 (chat: "Sim, 300k") on a measurement of 137 sessions
reported by the coordinating Stratics session: after a compaction a session restarts at about 106k tokens (p50), which
left about 62k of room at 200k; the modelled cost per turn is lowest around 260–300k, and is 18 % higher at 500k and
100 % higher at 1M. With the owner's `300000`, the doctor's 200k cap warned on every run. 500k or 1M stay a
per-session exception (`/autocompact`), never the default.

[HYPOTHESIS] The plan's limit weighs cache reads as the API list price does; if it weighs them less, the saving is
smaller than the share above.

## Change

- `platforms/tools/doctor.sh` § 6 (Claude), `ensure_claude_auto_compact` with `AUTO_COMPACT_WINDOW=300000`:
  - when `~/.claude/settings.json` has no `autoCompactWindow`, it writes the number `300000` and keeps every other key
    (`fix: claude autoCompactWindow set to 300000 in <path> (KIT-010)`);
  - the string `"200k"` an older doctor wrote is replaced by `300000`
    (`fix: claude autoCompactWindow "200k", a string Claude Code ignores, replaced by 300000 in <path> (KIT-010)`);
  - an integer from 100000 to 300000 is `ok`;
  - an integer above 300000, up to 1000000, is kept and reported as `warn`, because it is the owner's choice;
  - any other value (a string such as `"500k"` or `"auto"`, a number outside 100000–1000000, a boolean) is kept and
    reported as `warn`, because Claude Code ignores it;
  - a set `CLAUDE_CODE_AUTO_COMPACT_WINDOW` is reported as `warn`, because it overrides the file;
  - an unreadable `settings.json` is a `FAIL`, and the file is not rewritten.
- `platforms/tools/smoke.sh`: the stub-Claude doctor runs check the `fix` that writes the number on the first run, the
  `ok` on the second, that a `500000` set by the owner is kept with its `warn`, that a `"200k"` is replaced by `300000`,
  and that a `"500k"` is kept with the `warn` that Claude Code ignores it.

## Proof

`bash platforms/tools/check.sh`; `bash platforms/tools/smoke.sh`; `python3 platforms/ci/validations/check_kit.py --links`;
`platforms/tools/doctor.sh` against the owner's `~/.claude/settings.json` (`autoCompactWindow: 300000`) reports
`ok: claude autoCompactWindow 300000`.

## History

- 2026-10-12: confirmed (owner, chat of the Stratics architect session on Claude usage) and implemented.
- 2026-11-12: window raised to 300000 (owner, chat: "Sim, 300k"). The doctor writes a number, replaces the `"200k"`
  it wrote before, and reports any value Claude Code ignores.
