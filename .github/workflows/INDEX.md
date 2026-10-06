# workflows/ — kit CI

| Workflow | Trigger | What it does |
|---|---|---|
| `ci.yml` | push + PR | `check.sh`, `shellcheck`, `smoke.sh`, `check_kit.py --links` |
| `evals.yml` | workflow_dispatch + Monday 06:17 UTC | `claude plugin eval` per plugin, pinned model, report uploaded as an artifact; needs the `ANTHROPIC_API_KEY` secret |
| `gitleaks.yml` | push + PR | secrets scan |
| `release.yml` | tag `v*` | validates tag == `VERSION`, creates a release with the CHANGELOG section |
