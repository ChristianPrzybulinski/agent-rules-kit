# kit review-loop

The model-free half of the orchestrated implement-review-merge loop (decided in the project that runs it): the verdict contract and an example config for the loop tool. The model half (orchestrator, reviewer and child skills) lives in the project that runs the loop, not in the kit (KIT-038). The loop tool stays there too (`platform/review-loop/`) and moves to its own repository only on a trigger, never into the kit: the kit is instructions every agent loads and is changed by hand outside the loop, while the loop tool is a stateful service whose own changes the loop reviews ([KIT-024](../../../docs/features/KIT-024-loop-tool-destination.md)). Reader: the owner who starts the loop in a second project or hands it to a second collaborator.

## How to use

1. Copy the loop skills and templates from the project that already runs the loop (in its `platform/review-loop/skills/` and `platform/review-loop/templates/`).
   Each child type (implementer, reviewer, apply) preloads the kit skills its prompt relies on, by plugin-qualified name in its profile's `skills:` list (`guardrails:review`, `guardrails:git`; in a vendored project the names `sync-project.sh` gives the kit's own agents: `guardrails-pinned:<skill>`, or the plain copy's name): a bare `review` can resolve to Claude Code's bundled skill. Check one child transcript per type for the kit's base directory (#241).
2. Copy `verdict.schema.json` next to the project's loop tool and `config.example.json` to its `config.json`; fill every `<placeholder>` and the repo list, one entry per repo the loop gates (the backlog repo included). Every key the project's loop tool reads is present; placeholders are in angle brackets.
3. Keep machine paths out of the committed config: `${WORKSPACE_ROOT}` stays a placeholder, and the local clone paths live in an untracked overlay.
4. Create and pin the batch-log issue, set `batch_log_issue`, then say `start` to the architect session (the project's skill `loop-orchestrate`).

## Contents

| File | Use |
|---|---|
| `verdict.schema.json` | JSON Schema of a review verdict; the `schema` prefix and the `pr` repo name are project-neutral (`<project>-verdict/v1`, `<repo>#<number>`) |
| `config.example.json` | example loop config: proof allowlist, poll interval, two flagged rounds then `needs-human`, risk paths, labels, per-repo suites, dispatch limits |

## Unverified / limits

- The example config was derived from a running project's `config.json`; no second project has run it yet.
- `proof_allowlist` is a security boundary of the project: review every word before adding one.
