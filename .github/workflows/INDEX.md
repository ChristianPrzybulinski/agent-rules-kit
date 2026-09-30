# workflows/ — CI do kit

| Workflow | Gatilho | O que faz |
|---|---|---|
| `ci.yml` | push + PR | `check.sh` (modo completo), `shellcheck`, `check_kit.py --links` |
| `gitleaks.yml` | push + PR | varredura de segredos |
| `release.yml` | tag `v*` | valida tag == `VERSION`, cria release com a seção do CHANGELOG |
