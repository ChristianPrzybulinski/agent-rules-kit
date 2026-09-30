# Manutenção do kit

## Versionar

`VERSION` (semver) + entrada no `CHANGELOG.md` + tag `vX.Y.Z`. Push da tag dispara `.github/workflows/release.yml`, que valida tag == `VERSION` e cria a release com a seção do changelog — **releases são automáticas**, não crie release manual.

`LAYOUT_VERSION` (inteiro) bumpa quando muda a estrutura de pastas ou um destino de instalação — `refresh.sh` detecta e roda `install/all.sh --clean` (reinstalação completa). Mudança de conteúdo sem mudar layout → só `VERSION`.

## Adicionar conteúdo

| Tipo | Passos |
|---|---|
| regra | copiar `agents/templates/kit-rule.md` → `agents/rules/<domínio>/`, listar em `agents/rules/INDEX.md`, `check.sh` |
| knowledge | copiar `kit-knowledge.md` → `agents/knowledge/<domínio>/` (frontmatter com `verified` + `sources`), listar em `agents/knowledge/INDEX.md` |
| skill | copiar `kit-skill.md` → `agents/skills/<tipo>/<nome>/`, `name` = pasta, listar no INDEX do tipo e em `agents/skills/INDEX.md` |
| template | `agents/templates/<prefixo>-<nome>.md` (regex `^(spec|doc|project|kit)-`), listar em `agents/templates/INDEX.md` |
| índice | `kit-index.md` (só lista) ou `kit-readme.md` (explica) — nunca os dois na mesma pasta |

## Skills de terceiros (vendor)

Política: **nunca `npx skills add` direto nos agentes**. Atualizar uma skill vendorizada:

1. `git ls-remote https://github.com/<repo> HEAD` → novo SHA.
2. Atualizar a linha em `platforms/kits/third-party/skills.lock` (name | repo | path | sha | licença | data).
3. `platforms/install/third-party.sh` regenera `agents/skills/vendor/<name>/` + `VENDOR.md`.
4. `platforms/tools/check.sh` (lock × VENDOR.md × schema) → commit.

Remover: apagar a linha do lock + `git rm -r agents/skills/vendor/<nome>`.

## O que o CI exige

`.github/workflows/ci.yml`: `check.sh` com `CI=1` (pyyaml/jsonschema obrigatórios — local sem eles roda em modo estrutural com aviso), `shellcheck` nos `platforms/**/*.sh`, `check_kit.py --links`. `gitleaks.yml` em todo push. Dependabot semanal para actions.

Pré-requisitos desta máquina (2026-09-30): Godot 4.7.2 · JDK 25 (`/opt/homebrew/opt/openjdk@25`, keg-only — via `toolchains.xml`) e JDK 27 no PATH · Maven 3.9.16 · Node 26.10.0/npm 11.19.1 · Docker 29 + Compose v5 · gh 2.101 · git-lfs 3.8 · DBeaver · Krita. Python do sistema sem `pyyaml`/`jsonschema` (check roda em modo estrutural; CI instala).
