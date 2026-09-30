# tools/ — ciclo de vida do kit na máquina

| Arquivo | Escopo | Quando usar |
|---|---|---|
| `bootstrap.sh` | clona `~/.ai-kit` (gh, fallback https) e instala | primeira vez na máquina |
| `refresh.sh` | `git pull --ff-only` + reinstala se VERSION/LAYOUT_VERSION mudaram (layout → `--clean`) | início de sessão (`--quiet` sai em silêncio) |
| `check.sh` | valida o kit (`check_kit.py`); `--spec <dir>` valida `docs/spec` de um projeto | após qualquer mudança no kit; no CI |

Estado instalado: `~/.config/agent-rules-kit/{VERSION,LAYOUT_VERSION}`.
