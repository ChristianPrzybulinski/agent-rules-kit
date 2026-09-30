# third-party/ — skills externas pinadas

| Arquivo | Escopo |
|---|---|
| `skills.lock` | uma linha por skill: `name \| repo \| path \| commit-sha \| licença \| verificado` |

`platforms/install/third-party.sh` lê o lock e vendoriza em `agents/skills/vendor/<name>/` (com `VENDOR.md`). Atualizar: `git ls-remote` no repo → novo SHA no lock → `third-party.sh` → `check.sh`. Nunca `npx skills add` nos agentes.
