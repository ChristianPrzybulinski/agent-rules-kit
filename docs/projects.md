# O que vive num projeto que usa o kit

Regras, skills e conhecimento ficam **no kit** e são instalados na máquina (`platforms/install/`). O projeto só recebe artefatos próprios. Exemplo real: `~/Documents/GitHub/stratics-docs`.

## No projeto

| Artefato | Origem no kit | Exemplo (stratics-docs) |
|---|---|---|
| `AGENTS.md` do repo | `agents/templates/project-agents-*.md` preenchido | `AGENTS.md` (escopo, comandos, limites) |
| `docs/spec/` | criado por `platforms/kits/sdd/init-spec.sh`; artefatos seguem `agents/templates/spec-*` e schemas de `platforms/ci/schemas/` | `docs/spec/spec.md`, `features/FEAT-0nn.md`, `requirements/`, `decisions/`, `debts/` |
| `docs/sessions/` | `agents/templates/doc-session-handoff.md` | `docs/sessions/2026-09-30-specs-iniciais.md` |
| `docs/legacy/` (ou relatórios) | `agents/templates/doc-*.md` | `docs/legacy/evidencias.md` etc. |
| `.github/workflows/` | `platforms/kits/github/workflows/` | `spec-lint.yml` (faz checkout do kit e roda `platforms/tools/check.sh --spec docs/spec`), `gitleaks.yml`, `reusable-ci-*.yml` |
| `.github/PULL_REQUEST_TEMPLATE.md`, `CODEOWNERS`, labels | `platforms/kits/github/` | idem + `scripts/labels-sync.sh` |
| `infra/` / compose | `platforms/kits/docker/` | `infra/compose.yml` (`name: stratics`) |
| `.gitattributes` (LFS) | `platforms/kits/git-lfs/` | primeiro commit do repo |

IDs em `docs/spec/`: `FEAT-nnn`, `REQ-F-nnn`, `REQ-NF-nnn`, `DEC-nnn`, `DEBT-nnn` — numeração sequencial, `id` = prefixo do nome do arquivo, status no frontmatter (`proposta`/`aprovada`/`implementada`…). Processo: `agents/skills/process/README.md`.

## O que NÃO vai para o projeto

- Regras (`agents/rules/`), skills, knowledge: instaladas na máquina do agente — o projeto não copia.
- Schemas e validadores: o projeto referencia via checkout do kit no CI (`spec-lint.yml`), não duplica.
- Originais de acervo legado: só relatórios/manifestos entram no repo (regra do projeto, ver `docs/legacy/README.md` do stratics-docs).
