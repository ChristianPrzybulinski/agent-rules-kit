# kit review-loop

The model-free half of the orchestrated implement-review-merge loop (a project's DPRO-011): the verdict contract and an example config for the loop tool. The model half (orchestrator, reviewer and child skills) lives in the project that runs the loop, not in the kit (KIT-038). Reader: the owner who starts the loop in a second project or hands it to a second collaborator.

## How to use

1. Copy the loop skills and templates from the project that already runs the loop (Stratics: `platform/review-loop/skills/` and `platform/review-loop/templates/`).
2. Copy `verdict.schema.json` next to the project's loop tool and `config.example.json` to its `config.json`; fill every `<placeholder>` and the repo list, one entry per repo the loop gates (the backlog repo included). Every key the project's loop tool reads is present; placeholders are in angle brackets.
3. Keep machine paths out of the committed config: `${WORKSPACE_ROOT}` stays a placeholder, and the local clone paths live in an untracked overlay.
4. Create and pin the batch-log issue, set `batch_log_issue`, then say `start` to the architect session (skill `loop-orchestrate`).

## Contents

| File | Use |
|---|---|
| `verdict.schema.json` | JSON Schema of a review verdict; the `schema` prefix and the `pr` repo name are project-neutral (`<project>-verdict/v1`, `<repo>#<number>`) |
| `config.example.json` | example loop config: proof allowlist, poll interval, two flagged rounds then `needs-human`, risk paths, labels, per-repo suites, dispatch limits |

## Decision on the loop tool

The loop tool stays in the project (Stratics: `platform/review-loop/`, decided in its DPRO-011 amendment 2026-11-01d). It reads `config.json` but still hard-codes the project name in its state directory, verdict marker, review status context, the apply-owner rule, the `Closes` message, the spec-issue bodies and the integration repository list. The project splits it into a neutral engine that reads those values from config and a project profile; a boundary test fails when engine code names the project outside a shrinking allowlist.

- It moves to its own repository when a trigger holds and the boundary test is green with no project entry left in the allowlist: a second project is going to run the loop, a second OS needs its own release of the engine, or someone needs the engine without the project.
- It never moves into the kit: the kit is instructions every agent loads and is changed by hand outside the loop, while the loop tool is a stateful service whose own changes the loop reviews.
- The plugin skills say "the project's loop tool" and read its path from the project (`loop-orchestrate` § 0).

## Unverified / limits

- The example config was derived from a running project's `config.json`; no second project has run it yet.
- `proof_allowlist` is a security boundary of the project: review every word before adding one.
