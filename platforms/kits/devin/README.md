# kit devin

Templates for running Devin Cloud sessions reproducibly: one `environment.yaml` per stack, a snapshot checklist and the Playbooks derived from a project's review-loop child prompts (implement one issue, apply one fix round). Reader: the owner who creates the Devin snapshot and the library of a repository.

## How to use

1. Copy the matching `environment.godot.yaml`, `environment.java.yaml` or `environment.docs.yaml` to `environment.yaml` at the project root; edit the pinned versions to the project's.
2. Read `snapshot-checklist.md` before creating or refreshing the snapshot.
3. Attach `playbooks/implement-issue.devin.md` and `playbooks/fix-round.devin.md` to the Devin Playbook library; replace the `<placeholders>` once (owner, backlog repo, schema prefix, loop script).
4. Read `playbooks/devin-review-autofix.md` before enabling Devin Review autofix.

What a cloud child receives is `plugins/guardrails/AGENTS.md` plus `plugins/*/rules/` (the path-scoped rules), so the critical constraints live there and in the project `AGENTS.md`.

## Contents

| File | Destination |
|---|---|
| `environment.godot.yaml` | `environment.yaml` of a Godot 4 project (Godot 4.7.2 headless, export templates, git-lfs, gdtoolkit when `requirements-gdtoolkit.txt` exists) |
| `environment.java.yaml` | `environment.yaml` of a Java/Maven project (JDK 25 Temurin, Maven wrapper, offline warm-up, Docker for Testcontainers) |
| `environment.docs.yaml` | `environment.yaml` of a spec/docs repository (Python pins of the spec checks, git-lfs) |
| `snapshot-checklist.md` | read before the snapshot is created or refreshed |
| `playbooks/implement-issue.devin.md` | Devin Playbook library: implement one backlog issue in a worktree |
| `playbooks/fix-round.devin.md` | Devin Playbook library: apply a gates result, a verdict or a conflict notice |
| `playbooks/devin-review-autofix.md` | note: Devin Review autofix beside a Claude-reviewed loop |

## Devin Cloud facts (verified 2026-10-06, assessment §9.2)

- Plugin hooks and subagents load only in Devin CLI and Desktop, not in Devin Cloud.
- One skill is active at a time; `AGENTS.md` and `rules/` of a plugin are always on.
- Knowledge is deprecated in favour of skills in plugins; `environment.yaml` `knowledge` entries (a list of `name` and `contents`) are loaded into context at session start and never executed.
- Playbooks are still supported: attach one as `<name>.devin.md` at session start, call it from the library with the macro `!<name>`, or pass `playbook_id` on the API.

## Unverified / limits

- Verified on docs.devin.ai on 2026-10-06: the `environment.yaml` keys `initialize`, `maintenance`, `knowledge` and their shapes (`environment-yaml`), the playbook section names (`product-guides/creating-playbooks`) and the autofix bot setting (`work-with-devin/devin-review`).
- Not found there: the `<name>.devin.md` attachment name, the `playbook_id` API use and the 5-minute limits for `maintenance`, lint and tests (the only documented limit is 3 hours per step); verify before relying on them.
- `initialize` assumes an Ubuntu VM with `sudo` and `apt-get`; on a system Python that refuses `pip install` (PEP 668) use a venv. Docker on the VM and the `JAVA_HOME` export through `~/.bashrc` are unproven.
