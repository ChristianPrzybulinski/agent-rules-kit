# .github/ — kit CI and metadata

| Item | Scope |
|---|---|
| `workflows/` | `ci.yml` (check + shellcheck + install smoke + links), `devin-plugin.yml` (push to `main` → `devin-plugin` branch), `evals.yml` (on-demand `claude plugin eval`), `gitleaks.yml` (secrets), `release.yml` (tag `v*` → automatic release) |
| `dependabot.yml` | weekly actions updates |
| `PULL_REQUEST_TEMPLATE.md` | kit PR checklist |
| `CODEOWNERS` | `* @ChristianPrzybulinski` |
