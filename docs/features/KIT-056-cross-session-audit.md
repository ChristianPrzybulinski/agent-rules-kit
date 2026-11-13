---
id: KIT-056
title: "A weekly cross-session audit keeps agent memory current and promotes recurring lessons"
status: done
confirmed: "2026-11-12 (owner, chat of the session 'agent-rules-kit | new | architecture | cross-session learning audit': questions Q1-Q5, then \"Sim, abrir\" to opening the issue after runs A and B)"
issue: "#204"
pr: "#205"
---

# KIT-056 — A weekly cross-session audit keeps agent memory current and promotes recurring lessons

## Problem and evidence

[FACT] The `session` review mode sees one session. A signal that looks like a one-off inside one session is "not a signal" (`plugins/guardrails/skills/session/references/kit-proposal.md:22`), so a gap that recurs only across sessions is never proposed.

[FACT] Run A, 2026-11-12, audited the owner's Claude memory: 84 entries (17,366 bytes), which load into every Claude session of that folder. Codex and Devin never read them. Four read-only Sonnet subagents audited the entries for 371,877 tokens, and the orchestrator checked their claims.
- 67 of 84 entries need an action. For 22 of them the action was confirmed by a command or a file read.
- 38 are stale. Only 8 are expired one-night or one-batch authorizations. The other 30 mix a dated snapshot with a durable how-to.
- 11 duplicate another store. In 6 of them, the lesson was promoted by hand and the memory copy stayed behind.
- 14 hold a rule for a whole repository that is missing from that repository's `AGENTS.md`.
- 3 entries contradict each other on who approves a merge.
- 1 entry overrides a rule that two `AGENTS.md`-level files still state without the exception.

[FACT] Run B, 2026-11-12, used a standard-library pre-filter over the owner's transcripts from 2026-11-02 to 2026-11-12: 627 files (319 Claude Code, 308 Codex), 5.22 GB, 34.15 s, 61 MB peak RSS. A Sonnet step then read only the 55,326-char redacted extract: 47.9 s, 90,498 tokens.
- `ai-kit guard` blocked 147 `rm -rf` calls in 98 sessions. 94 of them (64%) targeted a temp or scratchpad path that the same command had just set. No kit text names a safe cleanup path.
- 3 sessions show the same owner correction about rerunning only what failed.
- Tool-call shape errors recurred across sessions: in 21, 8 and 7 sessions.
- The owner said they could not follow an explanation in 31 sessions. A memory rule that targets this is cited in 33 sessions.
- Only 3 `Kit [PROPOSAL]` blocks were written in 11 days. One of them is still open, and run A found the same gap independently.

[FACT] Only the combination ranks the work. Stale memory entries were cited in 123, 70 and 30 sessions in those 11 days, and the two leading promotion candidates in 96 and 69.

[FACT] The checks found model errors in both runs:
- a disproved "leaked secret";
- an active authorization labeled stale;
- a pattern with 1 real instance;
- an overcount.

Separately, a bare personal-topic keyword skipped 2 work sessions by mistake.

## Change

Delivery 1 needs a CHANGELOG line, not this record:
- `plugins/guardrails/skills/session/SKILL.md`: an `audit` mode.
- `plugins/guardrails/skills/session/references/cross-session-audit.md` (≤60 lines, `kind: detail`): the inputs, the expiry and promotion rules, the report shape, the check step and the privacy rules.
  - The check step: every claim the report relies on is re-checked before the owner sees it, and a claim nobody checked is tagged `[HYPOTHESIS]`.
  - Actions are sorted by the number of sessions that cite them.
  - Stale entries that are not pure expired authorizations go to a rewrite list.

Delivery 2 is this record.
- `platforms/tools/session_audit.py`: a pre-filter that uses no model tokens and only the standard library.
  - It reads the Claude Code jsonl and Codex rollouts changed since the last run, using byte offsets kept in its state.
  - It keeps:
    - the owner's correction messages, as redacted excerpts of at most 300 chars;
    - `Kit [PROPOSAL]` blocks;
    - normalized tool errors, counted by distinct session;
    - memory-entry citations per session;
    - blocked destructive commands classed by target (a temp path or another path), as counts only.
  - An exclude list (session id or title) and personal-topic keywords skip whole sessions. A keyword with a work meaning, such as `banco`, counts only next to a word that confirms the personal meaning.
  - It prints counts only. The extract goes to a private state directory with mode `0600`.
- `platforms/tools/refresh.sh`: it calls the pre-filter when the last stamp is 7 or more days old; `AI_KIT_SESSION_AUDIT=0` turns the call off, and a failure only warns. No new LaunchAgent is added, so the frozen layout keeps its installation destinations.
- The owner's local setup, documented in the reference: a weekly Claude desktop scheduled task runs the `audit` mode on the newest extract.

The audit's permissions (owner, Q3 and Q4):
- **Memory:** it archives only expired entries (one night, batch or session, older than 7 days). They move to `memory/archive/` and can be restored. Merging, rewriting and promotion wait for the owner's yes.
- **Repository `AGENTS.md`:** promotions go through a PR, only for entries cited in 5 or more sessions in a week.
- **Kit:** promotions arrive as `Kit [PROPOSAL]` blocks.

No always-on line is added (`docs/design.md:16`). Nothing from transcripts enters this repository.

## Proof

- `bash platforms/tools/check.sh`, `bash platforms/tools/smoke.sh`, `python3 platforms/ci/validations/check_kit.py --links`.
- Tests that `session_audit.py` adds, on synthetic fixtures:
  - a token-shaped string is redacted;
  - an excluded session and a personal-keyword session are skipped;
  - a work-meaning keyword without a confirming word does not skip;
  - a second run reads no old lines;
  - a Codex rollout is parsed;
  - a blocked `rm -rf` is classed by its target;
  - stdout holds only counts.
- One run on the owner's machine: counts printed, no value printed, extract mode `0600`.

## History

- 2026-11-12: confirmed (owner, Q1-Q5 of the design proposal).
- 2026-11-12: evidence refreshed from runs A and B; the owner approved opening the issue (#204).
- 2026-11-12: done; the `audit` mode, the reference, `session_audit.py` with `test_session_audit.py` and the `refresh.sh` call ship in one PR (#205).
