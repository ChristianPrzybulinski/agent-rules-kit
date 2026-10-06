# kit review-loop

The model-free half of the orchestrated implement-review-merge loop (a project's DPRO-011): the verdict contract and an example config for the loop tool. The model half is the `process-loop` plugin (`plugins/process-loop/INDEX.md`). Reader: the owner who starts the loop in a second project or hands it to a second collaborator.

## How to use

1. Install the plugin (`claude plugin install process-loop@ai-kit`, or `all`).
2. Copy `verdict.schema.json` next to the project's loop tool and `config.example.json` to its `config.json`; fill every `<placeholder>` and the repo list, one entry per repo the loop gates (the backlog repo included). Every key the project's loop tool reads is present; placeholders are in angle brackets.
3. Keep machine paths out of the committed config: `${WORKSPACE_ROOT}` stays a placeholder, and the local clone paths live in an untracked overlay.
4. Create and pin the batch-log issue, set `batch_log_issue`, then say `start` to the architect session (skill `loop-orchestrate`).

## Contents

| File | Use |
|---|---|
| `verdict.schema.json` | JSON Schema of a review verdict; the `schema` prefix and the `pr` repo name are project-neutral (`<project>-verdict/v1`, `<repo>#<number>`) |
| `config.example.json` | example loop config: proof allowlist, poll interval, two flagged rounds then `needs-human`, risk paths, labels, per-repo suites, dispatch limits |

## Decision on the loop tool

The loop tool stays in the project (a `ops/review-loop/loop.py` there): it reads `config.json` but still hard-codes the project name in its state directory, verdict marker, review status context, the apply-owner rule, the `Closes` message and the spec-issue bodies. It moves under `platforms/tools/` only after those literals read from config; until then the plugin skills say "the project's loop tool".

## Unverified / limits

- The example config was derived from a running project's `config.json`; no second project has run it yet.
- `proof_allowlist` is a security boundary of the project: review every word before adding one.
