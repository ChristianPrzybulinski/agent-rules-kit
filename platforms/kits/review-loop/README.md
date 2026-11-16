# kit review-loop

What the kit says to a project that runs the orchestrated implement-review-merge loop. The loop itself (tool, child prompts and skills, templates, verdict schema and example config) lives in its own repository, [dev-game-studio/review-loop](https://github.com/dev-game-studio/review-loop), under `platform/review-loop/`; the kit keeps no copy, since the kit is instructions every agent loads and is changed by hand outside the loop, while the loop tool is a stateful service whose own changes the loop reviews ([KIT-024](../../../docs/features/KIT-024-loop-tool-destination.md)). Reader: the owner who starts the loop in a second project or hands it to a second collaborator.

## How to use

1. Take the loop skills, templates, `verdict.schema.json` and the generic example config (`examples/generic/platform/loop-config/`) from that repository's `platform/review-loop/`.
   Each child type (implementer, reviewer, apply) preloads the kit skills its prompt relies on, by plugin-qualified name in its profile's `skills:` list (`guardrails:review`, `guardrails:git`): a bare `review` can resolve to Claude Code's bundled skill. Check one child transcript per type for the kit's base directory (#241).
2. Keep machine paths out of the committed config: `${WORKSPACE_ROOT}` stays a placeholder, and the local clone paths live in an untracked overlay.
3. `proof_allowlist` is a security boundary of the project: review every word before adding one.
4. Start a batch as that repository's `platform/review-loop/README.md` says (the pinned batch-log issue, `batch_log_issue`, then `start` to the orchestrator session).
