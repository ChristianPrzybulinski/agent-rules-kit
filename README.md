# Kit-IA — Regras, Skills e Prompts para Agentes de IA

Conjunto único de instruções lido por Devin, Windsurf, Cursor, Claude Code e adaptável a ChatGPT.

## Princípios de design (baseados em evidência)

- **Um always-on curto** (`AGENTS.md`, 60-150 linhas): stack, limites, disciplina. Estudos (GitHub 2.500 repos, ETH AGENTbench, Augment golden-PR) mostram queda de qualidade acima de ~300 linhas e ganho com listas numeradas, exemplos de 3-10 linhas e limites explícitos.
- **Condição → ação**, não valores vagos. "Antes de editar migration, verifique se já rodou" fira; "seja cuidadoso" não.
- **Conhecimento profundo em skills/regras sob demanda** (`model_decision`), não always-on.
- **Referenciar, não duplicar**: estilo vive em `pom.xml`/`.editorconfig`/`project.godot`, não nas regras.
- **Ordenado por meia-vida**: disciplina durável no topo; ferramentas (que mudam) no fim.

## Estrutura

```text
~/.ai-kit/
├── AGENTS.md                 # always-on global (Devin/Windsurf/Cursor/Codex/Copilot leem nativamente)
├── PROMPT.md                 # system prompt completo (GPTs, Projects, API)
├── PROMPT-compact.md         # ≤1.500 chars para Custom Instructions do ChatGPT
├── CHANGELOG.md
├── rules/                    # detalhe por domínio, carregado sob demanda (frontmatter trigger/description)
│   ├── 00-core.md            # evidência e ceticismo
│   ├── 10-clean-code.md
│   ├── 20-clean-architecture.md
│   ├── 30-java.md
│   ├── 40-godot-2d.md
│   ├── 50-github-cli.md
│   ├── 60-documentation.md
│   └── 70-token-efficiency.md
├── skills/                   # SKILL.md invocáveis por /nome ou pelo agente
│   ├── skeptic/              # verificação adversarial de afirmações (>98%)
│   ├── java/
│   ├── godot-2d/
│   ├── github-cli/
│   └── docs/
├── templates/                # AGENTS.md de projeto, por stack (copiar para a raiz do repo)
│   ├── java-spring/AGENTS.md
│   └── godot-2d/AGENTS.md
└── scripts/
    ├── install.sh            # instala em Devin, Windsurf, Cursor, Claude Code
    └── to-mdc.sh             # converte rules/*.md → .cursor/rules/*.mdc
```

## Instalação

```bash
~/.ai-kit/scripts/install.sh          # tudo (global)
~/.ai-kit/scripts/install.sh --check  # só valida frontmatter e tamanhos
```

O script faz:

| Destino | O que | Lido por |
|---|---|---|
| `~/.config/devin/AGENTS.md` | always-on | Devin |
| `~/.devin/rules/*.md` | regras sob demanda | Devin |
| `~/.config/devin/skills/*/SKILL.md` | skills | Devin |
| `~/.codeium/windsurf/memories/global_rules.md` | always-on | Windsurf |
| `~/.cursor/rules/*.mdc` | regras (convertidas) | Cursor |
| `~/.claude/CLAUDE.md` (só com `--claude`) | always-on | Claude Code |

Não instala em `~/.devin/global_rules.md` nem (por padrão) em `~/.claude/CLAUDE.md`: Devin lê ambos como regra global e carregaria o mesmo texto duas vezes. Use `--claude` apenas se usa Claude Code — e, nesse caso, desative a importação no Devin com `"read_config_from": {"claude": false}` em `~/.config/devin/config.json`.

### Por projeto

```bash
cp ~/.ai-kit/templates/java-spring/AGENTS.md ./AGENTS.md   # ou godot-2d
# edite os [colchetes]; opcional:
mkdir -p .devin && cp -r ~/.ai-kit/skills .devin/
```

### ChatGPT

- Custom Instructions → conteúdo de `PROMPT-compact.md`.
- GPT personalizado / Project → conteúdo de `PROMPT.md`.

## Uso

- `/skeptic <afirmação>` — verificação adversarial com veredicto e confiança.
- `/java`, `/godot-2d`, `/github-cli`, `/docs` — carregam o conhecimento do domínio.
- O agente também invoca essas skills sozinho quando o contexto casa (tabela em `AGENTS.md`).

## Manutenção

- Nova linha em `AGENTS.md` só se passar no teste: "remover isto mudaria um resultado amanhã?"
- `AGENTS.md` ≤ 150 linhas. Detalhe vai para `rules/` ou `skills/`.
- Lint opcional em repos: `npx agents-md-lint AGENTS.md` (Taiizor/agents-md-cookbook).
- Toda mudança relevante → `CHANGELOG.md` + rodar `install.sh`.

## Referências

- agents.md (padrão) · Taiizor/agents-md-cookbook · NasserAlbusaidi/claude.md (5 mecânicas) · GoranErhartic/cursor-development-rules · voxmedia/open-agent-toolkit (skeptic) · AKDworks/Godot-Clarity · Common-ka/godot-cursor-rules
