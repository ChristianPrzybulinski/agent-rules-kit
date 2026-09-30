# Schemas

JSON Schema (draft 2020-12) do **frontmatter YAML** dos artefatos de spec. Validados por `scripts/check.sh --spec <dir>` e pelo workflow `kits/github/workflows/spec-lint.yml`.

| Schema | Arquivo alvo | Regra de nome |
|---|---|---|
| `spec.schema.json` | `docs/spec/spec.md` | fixo |
| `feature.schema.json` | `docs/spec/features/*.md` | `FEAT-nnn-slug.md`; `id` = prefixo do nome |
| `requirement.schema.json` | `docs/spec/requirements/{functional,non-functional}/*.md` | `REQ-F-nnn-slug.md` em `functional/`; `REQ-NF-nnn-slug.md` em `non-functional/` |
| `decision.schema.json` | `docs/spec/decisions/*.md` | `DEC-nnn-slug.md` |
| `debt.schema.json` | `docs/spec/debts/*.md` | `DEBT-nnn-slug.md` |

Checagens além do schema (feitas pelo `check.sh`): `id` do frontmatter = prefixo do nome do arquivo; toda `REQ` referenciada por uma `FEAT` existe e vice-versa; IDs únicos; `FEAT.status` só avança (comparado com `git show HEAD:<arquivo>` quando existe).

Validador: `python3` + `jsonschema` + `pyyaml` se disponíveis; senão `check.sh` faz validação estrutural e avisa. Instalação opcional: `pip3 install --user jsonschema pyyaml`.
