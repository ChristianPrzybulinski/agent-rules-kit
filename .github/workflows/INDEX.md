# workflows/ — kit CI

| Workflow | Trigger | What it does |
|---|---|---|
| `ci.yml` | workflow_dispatch only (KIT-014) | `check.sh`, `shellcheck`, `smoke.sh`, `check_kit.py --links` |
| `evals.yml` | workflow_dispatch only | `claude plugin eval` per plugin, pinned model, report uploaded as an artifact; needs the `ANTHROPIC_API_KEY` secret |
| `gitleaks.yml` | workflow_dispatch only (KIT-014) | secrets scan |
| `release.yml` | tag `v*` | validates tag == `VERSION`, creates a release with the CHANGELOG section |
