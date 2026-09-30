# validations/ — scripts de validação

| Arquivo | Escopo | Chamado por |
|---|---|---|
| `check_kit.py` | invariantes do kit (layout, frontmatter, índices, links, lock, duplicação, prompt compact) | `platforms/tools/check.sh`, CI do kit |
| `check_spec.py` | `docs/spec/` de um projeto contra `../schemas/` | `check.sh --spec`, workflow spec-lint dos projetos |
