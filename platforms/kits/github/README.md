# kit github

Templates de CI, PR e governança de labels para GitHub Actions.

## Como usar

| Arquivo | Destino no projeto |
|---|---|
| `workflows/*.yml` | `.github/workflows/` |
| `PULL_REQUEST_TEMPLATE.md` | `.github/PULL_REQUEST_TEMPLATE.md` |
| `CODEOWNERS` | `.github/CODEOWNERS` (edite o usuário) |
| `labels.json` | referência para `scripts/labels-sync.sh` |
| `scripts/labels-sync.sh` | rode de qualquer lugar dentro do repo: `bash platforms/kits/github/scripts/labels-sync.sh` |

## Notas

- `ci-java.yml` assume Maven wrapper (`./mvnw`), JDK 25 Temurin e gates do `platforms/kits/java-maven/pom-parent.xml` (Spotless, JaCoCo, PITest). `dependency-check` roda em job separado com cache da base NVD.
- `ci-godot.yml` usa `barichello/godot-ci:4.7.2` (tag verificada no Docker Hub em 2026-09-29). Testes GUT só rodam se `addons/gut` existir. Export Windows/macOS só via `workflow_dispatch` e exige `export_presets.cfg` commitado no repo.
- `spec-lint.yml` clona este kit (privado) no PR para validar `docs/spec/**` contra `schemas/`. `GITHUB_TOKEN` basta para repo do mesmo owner; se falhar, use um PAT com scope `repo` em secret próprio (ex.: `KIT_PAT`).
- `gitleaks.yml` precisa de `fetch-depth: 0` para varrer o diff do PR inteiro.
