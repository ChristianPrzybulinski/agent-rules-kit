# agent-rules-kit — índice

Versão: ver `VERSION` · Layout: ver `LAYOUT_VERSION` (muda → reinstalação completa) · Histórico: `CHANGELOG.md`.

Kit de regras, conhecimento, skills e ferramentas para agentes de IA (Devin, Cursor, Windsurf, Codex, ChatGPT) trabalharem com o mesmo comportamento. Um lugar para cada coisa; nada duplicado. Se um conteúdo cabe em duas pastas, a tabela abaixo decide.

## As três pastas

| Pasta | O que é | Quem consome | Regra de admissão |
|---|---|---|---|
| [`agents/`](agents/INDEX.md) | Tudo que entra **no contexto do agente**: instruções always-on, regras, fatos, skills, templates que o agente preenche, prompts | o modelo, em sessão | Só entra se muda um comportamento do agente. Cada arquivo tem frontmatter com `description` + `trigger` e limite de linhas. |
| [`platforms/`](platforms/INDEX.md) | Tudo que **roda na máquina ou no CI**: instaladores, bootstrap/refresh, validações, schemas, kits de configuração copiados para projetos | shell, CI, humano | Só entra se é executável ou configuração de ferramenta. Nada aqui é lido pelo agente como instrução. |
| [`docs/`](docs/INDEX.md) | Documentação **sobre o kit**: princípios de design, o que vive nos projetos, manutenção e versionamento | humano (e agente só quando mantém o kit) | Explica o kit; não instrui o agente em tarefas de projeto. |

## Dentro de `agents/` — não confundir

| Conteúdo | Pergunta que responde | Formato | Não é |
|---|---|---|---|
| `AGENTS.md` | "Como me comporto sempre?" | ≤110 linhas, always-on, único | lugar de detalhe |
| `rules/` | "O que DEVO/NÃO DEVO fazer neste domínio?" | normativo, ≤60 linhas, sob demanda | explicação nem fato datado |
| `knowledge/` | "Qual é o fato verificado (versão, quota, API) e a fonte?" | factual, datado, ≤40 linhas, com URL | regra nem opinião |
| `skills/` | "Como executo esta tarefa passo a passo?" | procedimento invocável `/nome`, com entradas/saídas/critério de pronto | regra genérica |
| `templates/` | "Que forma tem este artefato?" | esqueleto com `[colchetes]`, um por tipo de artefato | conteúdo pronto |
| `prompts/` | "O que colo em ferramenta sem suporte a AGENTS.md?" | texto compilado do AGENTS.md | fonte de verdade (é derivado) |

Teste rápido: regra tem verbo modal ("deve", "nunca"); knowledge tem data e URL; skill tem etapas numeradas e "pronto quando"; template tem colchetes.

## Dentro de `platforms/`

| Pasta | Escopo |
|---|---|
| `install/` | instala `agents/` nas ferramentas (Devin, Cursor, Windsurf, Codex) e vendoriza skills externas |
| `tools/` | `bootstrap.sh` (primeira vez) · `refresh.sh` (toda sessão) · `check.sh` (valida o kit) |
| `ci/` | `schemas/` (JSON Schema de todo frontmatter e de specs de projeto) · `validations/` (scripts que o CI e o `check.sh` rodam) |
| `kits/` | arquivos prontos para copiar em projetos: Maven parent, Compose, workflows, LFS, labels |

## Ordem de leitura

1. Este arquivo.
2. `agents/AGENTS.md` — o que vale sempre.
3. `agents/INDEX.md` → a regra/skill do seu contexto.
4. Vai criar/alterar o kit? `docs/maintenance.md` primeiro.

## Invariantes (validadas por `platforms/tools/check.sh` e pelo CI)

- Toda pasta tem `INDEX.md` (lista + quando usar) ou `README.md` (precisa explicar mais); nunca os dois.
- Todo arquivo de `agents/` tem frontmatter válido pelo schema do seu tipo e respeita o limite de linhas.
- Todo link relativo aponta para arquivo existente; todo arquivo de uma pasta aparece no índice dela.
- Nenhum conteúdo repetido entre `AGENTS.md`, `rules/`, `knowledge/`, `skills/`: resumo no `AGENTS.md`, detalhe em um só lugar, referência nos demais.
