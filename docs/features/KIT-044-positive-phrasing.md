---
id: KIT-044
title: "Soft rules of core AGENTS.md say what to do instead of what not to do"
status: done
confirmed: "2026-11-11 (owner's kit review, night brief item 9; recommendations approved in chat until revoked)"
issue: "#165"
pr: "#166"
---

# KIT-044 — Soft rules of core AGENTS.md say what to do instead of what not to do

## Problem and evidence

[FACT] Anthropic's "Claude prompting best practices" (platform.claude.com, section "Control the format of
responses") says: "Tell Claude what to do instead of what not to do." The same page warns that aggressive emphasis
makes newer models overtrigger. At `b46e96c`, `plugins/core/AGENTS.md`, which every session loads, had 9 soft-rule
clauses phrased as a prohibition, each next to a positive instruction that already says what to do, so the
prohibition repeated the rule as a negative and added emphasis without adding behavior.

## Change

`plugins/core/AGENTS.md`, same meaning, no new rule:

| Before | After |
|---|---|
| "stop and name the exact path; never widen the scope silently." | "stop and name the exact path before touching it." |
| "warn and stop: follow-up or new session; never mix silently." | "say so and offer a follow-up or a new session before starting it." |
| "Same error twice → stop varying blindly; before the 3rd attempt" | "Same error twice → before the 3rd attempt" |
| "conclusion first, fluid, no AI clichés, no fabricated facts." | "conclusion first, plain and fluid, every fact sourced." |
| "tags kept, never compressed, even inside a technical answer." | "tags kept whole, even inside a technical answer." |
| "Tokens come from keychain/env; never typed or echoed in chat/terminal." | "Tokens come from keychain/env and stay out of chat and terminal output." |
| "tagged `[HYPOTHESIS]` in the answer and never stated as fact." | "tagged `[HYPOTHESIS]` in the answer." |
| "with 2-4 options and a recommendation, never a questionnaire." | "with 2-4 options and a recommendation." |
| "recommend. Never accept for the sake of accepting." | "recommend; agree on evidence." |

Kept on purpose:

- The Boundaries `**Never**:` line: a hard boundary in the Always / Ask first / Never pattern, where the negative is the
  rule.
- "never a mounted installer" in Browser automation: a concrete trap with the right path named before it.
- The glob rules `plugins/dev/rules/java.md`, `plugins/dev/rules/godot.md` and `plugins/sdd/rules/spec.md`: each
  "Never: X" already names the alternative after it.
- `plugins/sdd/skills/sdd-implement/references/task-pr.md:25` ("never widen the cell silently"): skill detail, loaded
  only with its procedure.

## Proof

- `plugins/core/AGENTS.md` stays at 59 lines (limit 60); `git diff --stat` shows 8 insertions and 8 deletions.
- Kit gates: see the PR body.

## History

- 2026-11-11: confirmed (owner's kit review); issue #165.
- 2026-11-11: done in #166.
