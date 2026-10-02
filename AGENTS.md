# agent-rules-kit — maintainer rules

This repository is the source of the `ai-kit` plugin. The plugin root is `kit/` (`AGENTS.md`, `rules/`, `skills/`, `templates/`, manifests); everything else is tooling and documentation.

- Global rules for every session come from `kit/AGENTS.md` through the installed plugin; never duplicate them here.
- Before a PR: `platforms/tools/check.sh` and `platforms/tools/smoke.sh` must pass (CI runs them with `CI=1`).
- Content changes follow `docs/maintenance.md`.
- Never add non-rule files to `kit/rules/`; never create `kit/agents/` (reserved by Devin for subagents).
