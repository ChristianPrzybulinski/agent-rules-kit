# .github/ — kit CI and metadata

| Item | Scope |
|---|---|
| `workflows/` | `ci.yml` (on-demand check + shellcheck + install smoke + links), `evals.yml` (on-demand `claude plugin eval`), `gitleaks.yml` (on-demand secrets scan), `release.yml` (tag `v*` → automatic release) |
| `dependabot.yml` | weekly actions updates |
| `PULL_REQUEST_TEMPLATE.md` | kit PR checklist |
| `CODEOWNERS` | `* @ChristianPrzybulinski` |
