# agents/ — o que entra no contexto do agente

Escopo: só conteúdo que muda um comportamento do agente. Cada arquivo carrega sob demanda pela sua `description`/`trigger`; o único always-on é `AGENTS.md`. Definições e teste rápido de "onde vai o quê": [`../INDEX.md`](../INDEX.md).

| Pasta | Escopo | Limite | Template | Schema |
|---|---|---|---|---|
| `AGENTS.md` | disciplina durável, roteamento para o resto | ≤110 linhas | — | — |
| [`rules/`](rules/INDEX.md) | normativo por domínio (core, development, architecture, java, godot, git, security, documentation) | ≤60 linhas cada | `templates/kit-rule.md` | `platforms/ci/schemas/rule.schema.json` |
| [`knowledge/`](knowledge/INDEX.md) | fatos datados com fonte (versões, quotas, APIs, glossários) | ≤40 linhas cada | `templates/kit-knowledge.md` | `knowledge.schema.json` |
| [`skills/`](skills/INDEX.md) | procedimentos invocáveis, por tipo: `quality` · `development` · `documentation` · `process` · `tooling` · `vendor` | ≤80 linhas (próprias) | `templates/kit-skill.md` | `skill.schema.json` |
| [`templates/`](templates/INDEX.md) | esqueletos de artefatos: `spec-*` (docs/spec dos projetos) · `doc-*` (relatórios, passagens, checklists) · `project-*` (AGENTS.md de projeto) · `kit-*` (conteúdo deste kit) | — | — | nome por regex |
| [`prompts/`](prompts/INDEX.md) | derivados do `AGENTS.md` para ChatGPT (compact/full) | — | — | — |

## Quando o agente carrega o quê

| Situação | Carrega |
|---|---|
| Toda sessão | `AGENTS.md` (e roda `platforms/tools/refresh.sh --quiet`) |
| Contexto bate com a `description` de uma regra | a regra — uma por vez, a mais específica |
| Precisa de número/versão/URL | a knowledge note do domínio |
| Vai executar um procedimento com etapas | a skill (`/nome`) |
| Vai criar FEAT/REQ/DEC/DEBT/relatório | o template correspondente |

Duplicação é bug: se um texto aparece em dois arquivos daqui, um deles referencia o outro.
