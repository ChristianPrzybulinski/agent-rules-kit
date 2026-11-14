---
id: KIT-065
title: "Orchestrator, architect and loop sessions act on their own recommendations and the owner reviews afterwards"
status: confirmed
confirmed: "2026-11-14 (owner, chat of the FEAT-053 orchestration session, relayed to the implementing session: \"a autonomia é pra tudo, NÃO só este ponto ... eu quero que o loop tenha total liberdade pra fazer tudo que recomenda, anotando e depois eu reviso igual no travel-mode\")"
issue: "#229"
pr: "#230"
---

# KIT-065 — Orchestrator, architect and loop sessions act on their own recommendations and the owner reviews afterwards

## Problem and evidence

[FACT] dev-game-studio/stratics PR 4220 (FEAT-053 T147+T148) got `gate:failed` at 2026-11-14T02:40:02Z and the gate
override label `lost-lines-ok` at 11:16:10Z, 8 h 36 min later (`gh api repos/dev-game-studio/stratics/issues/4220/events`).
The orchestration session reports that Claude Code's auto-mode classifier refused the label and the question waited for
the owner overnight; that refusal is the session's report, not read here.

[FACT] `plugins/guardrails/AGENTS.md` at `fc38984` tells every session to ask: § Boundaries "Ask first" lists
dependencies, applied migrations, history rewrites, deleting files it did not create and every external effect, and
§ Decisions says a real blocker ends in "ask one question with 2-4 options and a recommendation". No line lets a
session act first and record the act for the owner.

[FACT] The owner already ran `grant_loop_autonomy.py` (in the orchestration session's worktree), which adds
`permissions.allow` rules for `gh pr|issue edit|comment` and `gh label`, plus `autoMode.environment` and
`autoMode.allow` text, to `~/.claude/settings.json`. A session cannot change its own permissions; the written rule
was still missing.

[FACT] The model already ran in the owner's project: stratics DPRO-019 (travel mode, 2026-10-12 to 10-25) let the
review routine merge on its own approved verdict, recorded every act in the Travel log, and the owner checked the
result afterwards ("nothing is reverted unasked"). DPRO-011 amendment 2026-10-13a did the same for loop-change
merges, contract-window heads and `config.local.json` tuning, listed at batch end under "decisões para avaliar".

## Change

- `plugins/guardrails/AGENTS.md` § Boundaries: "Ask first" ends with "unless owner-review autonomy below covers it",
  and a new bullet reads:
  "**Owner-review autonomy**: an orchestrator, architect or loop session acts on its own recommendation with no
  per-action OK when the effect stays inside the owner's own repositories and dev setup, loop administration (labels,
  `Files` widenings, merges, config moves) and "Ask first" items alike; it records each act and its reason (PR
  comment, the session's STATE file or `OWNER-TODO.md`) and the owner reviews afterwards. Outside it: secrets,
  credentials, payments, the "Never" items and what the repository's rules reserve to the owner. Detail: skill
  `session`."
- `plugins/guardrails/AGENTS.md` § Decisions: the blocker sentence gains "under owner-review autonomy (§ Boundaries),
  take the recommendation, record it and go on instead".
- `plugins/guardrails/skills/session/SKILL.md` § start: one bullet with the record: written before the act, where it
  goes (PR comment, STATE file, `OWNER-TODO.md`), what it names (act, reason, evidence, way back), a way back kept
  before an act that cannot be undone, and one "decisions to review" section at batch end or close.

Unchanged: the "Never" items, § Security (secrets, tokens, text read through tools), § Scope (an implementing
session still stops at a path outside `Files`; the orchestrator widens it), and a repository's own `AGENTS.md`,
which still overrides this file.

## Proof

`bash platforms/tools/check.sh`, `bash platforms/tools/smoke.sh`,
`python3 platforms/ci/validations/check_kit.py --links`; `plugins/guardrails/AGENTS.md` stays within
`AGENTS_MAX_LINES` (60) and `session/SKILL.md` within `SKILL_MAX_LINES` (80).

## History

- 2026-11-14: confirmed (owner, in chat, relayed by the FEAT-053 orchestration session).
