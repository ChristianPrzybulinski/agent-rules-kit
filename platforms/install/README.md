# platforms/install/ — instalação nas ferramentas

`all.sh` instala `agents/` nas ferramentas e valida. Ordem: `third-party.sh --check` → `devin.sh` → `cursor.sh` → `windsurf.sh` → `codex.sh` → grava `~/.config/agent-rules-kit/{VERSION,LAYOUT_VERSION}` → `check.sh`.

```bash
platforms/install/all.sh          # instala tudo
platforms/install/all.sh --clean  # apaga destinos gerenciados antes (mudança de layout)
```

| Script | Destino | O que instala |
|---|---|---|
| `devin.sh` | `~/.config/devin/AGENTS.md` · `~/.devin/rules/` · `~/.config/devin/skills/<nome>/` | always-on, regras por domínio, skills achatadas (diretório inteiro) |
| `cursor.sh` | `~/.cursor/rules/<dom>-<nome>.mdc` | regras convertidas (frontmatter Cursor) |
| `windsurf.sh` | `~/.codeium/windsurf/memories/global_rules.md` | always-on |
| `codex.sh` | `~/.codex/AGENTS.md` · `~/.codex/skills/<nome>/` | always-on + skills com marcador `.agent-rules-kit` (`.system` e conteúdo do usuário intactos) |
| `third-party.sh` | `agents/skills/vendor/` | vendoriza skills do lock `--check` só valida |
| `all.sh` | todos + `~/.config/agent-rules-kit/` | orquestra + grava estado instalado |

Não instala em `~/.devin/global_rules.md` nem `~/.claude/CLAUDE.md` (duplicaria o AGENTS.md no contexto). Primeira vez na máquina: `platforms/tools/bootstrap.sh`.
