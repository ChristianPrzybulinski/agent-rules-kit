# platforms/ci/ — schemas e validações

`schemas/`: JSON Schema (draft 2020-12) de todo frontmatter do kit e dos artefatos `docs/spec/` dos projetos. `validations/`: scripts rodados por `platforms/tools/check.sh` e pelo CI do kit e dos projetos.

| Schema | Valida | Regra de nome do arquivo alvo |
|---|---|---|
| `rule.schema.json` | `agents/rules/**/*.md` | `description` com "Carregar"/"Usar"; `globs` obrigatório se `trigger: glob` |
| `knowledge.schema.json` | `agents/knowledge/**/*.md` | `verified` (data) + `sources` (URLs) obrigatórios |
| `skill.schema.json` | `agents/skills/<tipo>/<nome>/SKILL.md` (não-vendor) | `name` = pasta; `version` x.y; `triggers` |
| `skills-lock.schema.json` | linhas de `platforms/kits/third-party/skills.lock` | `sha` de 40 hex |
| `spec.schema.json` | `docs/spec/spec.md` do projeto | fixo |
| `feature.schema.json` | `docs/spec/features/*.md` | `FEAT-nnn-slug.md` |
| `requirement.schema.json` | `docs/spec/requirements/{functional,non-functional}/*.md` | `REQ-F-nnn-*` / `REQ-NF-nnn-*` |
| `decision.schema.json` | `docs/spec/decisions/*.md` | `DEC-nnn-slug.md` |
| `debt.schema.json` | `docs/spec/debts/*.md` | `DEBT-nnn-slug.md` |

Os 5 de spec (`spec`, `feature`, `requirement`, `decision`, `debt`) vão para os projetos **como cópia**: `platforms/tools/sync-project.sh` instala `check_spec.py` + schemas em `.github/spec-lint/` do projeto, e o workflow `platforms/kits/github/workflows/spec-lint.yml` os roda localmente — sem checkout nem token do kit.

| Validação | Escopo |
|---|---|
| `validations/check_kit.py` | layout v4, frontmatters, índices, links, lock, duplicação (`--links` inclui `~/.ai-kit/...`) |
| `validations/check_spec.py` | `docs/spec` de um projeto: schema + id=prefixo + cruzamento FEAT↔REQ + IDs únicos |

Sem `pyyaml`/`jsonschema`: validação estrutural com AVISO; com `CI=1`, ausência é erro.
