# platforms/ — o que roda na máquina e no CI

Escopo: executáveis e configuração de ferramenta. Nada aqui é instrução para o agente; o agente só **executa** o que está aqui (instalar, validar, atualizar).

| Pasta | Escopo | Entrada principal |
|---|---|---|
| [`install/`](install/README.md) | instala `agents/` nas ferramentas; vendoriza skills externas pinadas | `all.sh` |
| [`tools/`](tools/INDEX.md) | ciclo de vida do kit na máquina | `bootstrap.sh` (1ª vez) · `refresh.sh` (toda sessão) · `check.sh` (validar) |
| [`ci/`](ci/README.md) | schemas de todo frontmatter e das specs de projeto; scripts de validação usados por `check.sh` e pelos workflows | `validations/check_kit.py` · `validations/check_spec.py` |
| [`kits/`](kits/INDEX.md) | arquivos prontos para copiar em projetos (Maven parent, Compose, workflows, LFS, labels, lock de skills externas) | por kit |

## Onde cada coisa é instalada

| Destino | Conteúdo | Gerenciado por |
|---|---|---|
| `~/.config/devin/AGENTS.md` · `~/.config/devin/skills/<nome>/` · `~/.devin/rules/` | Devin | `install/devin.sh` |
| `~/.cursor/rules/*.mdc` | Cursor (regras convertidas) | `install/cursor.sh` |
| `~/.codeium/windsurf/memories/global_rules.md` | Windsurf | `install/windsurf.sh` |
| `~/.codex/AGENTS.md` · `~/.codex/skills/<nome>/` | Codex | `install/codex.sh` |
| `~/.config/agent-rules-kit/{VERSION,LAYOUT_VERSION}` | estado instalado, lido por `refresh.sh` | `install/all.sh` |

`LAYOUT_VERSION` diferente do instalado → `refresh.sh` apaga os destinos gerenciados e reinstala tudo. `VERSION` diferente → só reinstala. Igual → sai em silêncio.
