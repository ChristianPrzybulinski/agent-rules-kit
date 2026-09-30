# O que vive num projeto que usa o kit

Regras, skills e conhecimento ficam **no kit** e são instalados na máquina (`platforms/install/`). O projeto só recebe artefatos próprios. Exemplo real: `~/Documents/GitHub/stratics-docs`.

## No projeto

| Artefato | Origem no kit | Exemplo (stratics-docs) |
|---|---|---|
| `AGENTS.md` do repo | `agents/templates/project-agents-*.md` preenchido | `AGENTS.md` (escopo, comandos, limites) |
| `docs/spec/` | criado por `platforms/kits/sdd/init-spec.sh`; artefatos seguem `agents/templates/spec-*` e schemas de `platforms/ci/schemas/` | `docs/spec/spec.md`, `features/FEAT-0nn.md`, `requirements/`, `decisions/`, `debts/` |
| `docs/sessions/` | `agents/templates/doc-session-handoff.md` | `docs/sessions/2026-09-30-specs-iniciais.md` |
| `docs/legacy/` (ou relatórios) | `agents/templates/doc-*.md` | `docs/legacy/evidencias.md` etc. |
| `.github/spec-lint/` | cópia gerada por `platforms/tools/sync-project.sh` (`check_spec.py` + schemas + `KIT_VERSION`) | validação local de spec no CI do projeto |
| `.github/workflows/` | `platforms/kits/github/workflows/` | `spec-lint.yml` (roda a cópia local — sem checkout/token do kit), `gitleaks.yml`, `reusable-ci-*.yml` |
| `.github/PULL_REQUEST_TEMPLATE.md`, `CODEOWNERS`, labels | `platforms/kits/github/` | idem + `scripts/labels-sync.sh` |
| `infra/` / compose | `platforms/kits/docker/` | `infra/compose.yml` (`name: stratics`) |
| `.gitattributes` (LFS) | `platforms/kits/git-lfs/` | primeiro commit do repo |

IDs em `docs/spec/`: `FEAT-nnn`, `REQ-F-nnn`, `REQ-NF-nnn`, `DEC-nnn`, `DEBT-nnn` — numeração sequencial, `id` = prefixo do nome do arquivo, status no frontmatter (`proposta`/`aprovada`/`implementada`…). Processo: `agents/skills/process/README.md`.

## O que NÃO vai para o projeto

- Regras (`agents/rules/`), skills, knowledge: instaladas na máquina do agente — o projeto não copia.
- Schemas e validadores de spec chegam ao projeto como **cópia deliberada** em `.github/spec-lint/` (sem link com o kit no CI — o repo do kit pode até nem existir no momento do CI). Atualizar: `sync-project.sh <repo>`; divergência detectável com `sync-project.sh --check`. Workflows reutilizáveis **entre repos do mesmo produto** (ex.: `stratics-client` → `stratics-docs/.github/workflows/reusable-ci-*.yml`) são permitidos — o que se evita é depender do kit.
- Originais de acervo legado: só relatórios/manifestos entram no repo (regra do projeto, ver `docs/legacy/README.md` do stratics-docs).
