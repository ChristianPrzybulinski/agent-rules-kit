# 2026-10 kit assessment — report and execution prompts

Assessment of agent-rules-kit v10.1.0 (2026-10-06) against current Anthropic (Claude Code 2.1.x, Agent Skills), Cognition (Devin) and market guidance, measured against how the kit is used by the Stratics repositories (Godot 4.7 2D client, Java 25 / Spring Boot 4.1 server, spec repository). The Portuguese original was delivered to the owner in the assessment session; this folder holds the English version and the execution plan.

| Entry | Content |
|---|---|
| [`assessment.md`](assessment.md) | the full report: what is right, what is wrong, market comparison, changes A–G, additions N1–N7, prioritized plan, sources and limits |
| [`prompts/`](prompts/README.md) | 34 self-contained execution prompts, one per plan item, grouped in three phases; the index lists order, dependencies and touched files |

## How to execute a prompt

1. Pick the next prompt from [`prompts/README.md`](prompts/README.md) whose dependencies are merged. Phase 1 items are independent of each other except where the index says otherwise.
2. Open a fresh session (Claude Code or Devin) in a clone of the target repository named in the prompt header. Paste the whole prompt file as the first message, or point the session at the file path when the kit is checked out next to the repository.
3. The session creates the branch named in the header from an updated `main`, makes the change, runs every acceptance criterion and the gates listed in the prompt, and opens a PR with the body format the prompt asks for. It never pushes to `main`, never force-pushes, and never edits files outside the prompt's scope; a needed change outside the scope is reported as a blocker, not made.
4. Review the PR against the prompt's acceptance criteria (the diff is the evidence, not the session's report). Merge, then pick the next prompt.

## Phases

| Phase | Intent | Items |
|---|---|---|
| 1 | no layout change; remove contradictions that cost review rounds; make the hook cover what the skills promise; absorb the project's process deltas | P1-01 … P1-08 |
| 2 | distribute the kit by repository commit (works in cloud sessions, CI and new machines); rules with content; derived spec status; fewer, sharper skills; Java facts | P2-01 … P2-15 |
| 3 | Godot online 2D references and tooling; Devin environment and playbooks; spec regimes and a prototype lane; process-loop plugin; evals and KPIs | P3-01 … P3-11 |

## Measuring the effect

Compare two review-loop batches before and after phase 1 using the ledger (`ops/review-loop` in the spec repository): first-pass approval rate, rounds per PR and the share of findings owned by `spec`. Targets proposed in the assessment §8: first-pass approval ≥ 60% (39% at assessment time) and spec-caused findings ≤ 25%. If phase 1 does not move these numbers, the assessment's hypothesis that kit contradictions cost rounds is refuted and the effort should go to task cutting (P1-08, P2-08) first.

## Conventions for every prompt session

- Everything committed is in English; conversation with the owner is in pt-BR.
- The 10.x layout is frozen: no path or install-destination change in any prompt.
- `VERSION` is untouched; each PR adds a `## [Unreleased]` CHANGELOG entry with evidence.
- Kit gates: `platforms/tools/check.sh`, `platforms/tools/smoke.sh`, the unittest step and `check_kit.py --links` (see each prompt).
