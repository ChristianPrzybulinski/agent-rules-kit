# workflows/ — kit CI

| Workflow | Trigger | What it does |
|---|---|---|
| `ci.yml` | push + PR | `check.sh`, `shellcheck`, `smoke.sh`, `check_kit.py --links` |
| `gitleaks.yml` | push + PR | secrets scan |
| `release.yml` | tag `v*` | validates tag == `VERSION`, creates a release with the CHANGELOG section |
