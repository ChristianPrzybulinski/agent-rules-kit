---
name: sdd-constitution
version: "1.0"
description: Etapa 0 do SDD — cria (ou revisa) a constituição do projeto - AGENTS.md do repo com princípios verificáveis e docs/spec/spec.md com visão, escopo, glossário e índice. Usar uma vez por projeto novo, ou quando princípios mudam.
argument-hint: "[descrição do produto e stack, ou 'revisar']"
triggers:
  - user
allowed-tools:
  - read
  - glob
  - grep
  - write
  - edit
  - exec
---

# SDD 0 — Constitution

Referência: `agents/skills/process/README.md`. Templates: `agents/templates/project-agents-*.md`, `agents/templates/spec-index.md`.

## Pré-requisitos

- Repo inicializado. Se já existe `AGENTS.md` ou `docs/spec/`, **não sobrescreva**: leia e proponha diff.
- Decisões de stack já tomadas pelo produto (linguagem, engine, banco). Se faltar, pergunte — é decisão de produto.

## Etapas

1. Ler README, estrutura de pastas, manifestos (`pom.xml`, `project.godot`, `compose.yml`) — o que o agente **não consegue inferir** é o que entra no `AGENTS.md`.
2. Escolher o template de projeto mais próximo; preencher `[colchetes]` só com fatos verificados (versões reais instaladas/fixadas). Sem fato → `[HIPÓTESE: ...]`.
3. `AGENTS.md` do repo: ≤150 linhas. Seções: Stack · Comandos · Estrutura · Padrões (condição→ação) · Limites (Sempre/Perguntar/Nunca) · Sessões (como registrar progresso) · Onde está o resto. Regras globais do kit **não** se repetem aqui.
4. `docs/spec/spec.md` a partir do template: visão (3 linhas), fora de escopo explícito, glossário inicial, índices vazios.
5. Criar pastas `features/ requirements/functional requirements/non-functional decisions/ debts/` com `.gitkeep`.
6. Se o produto trouxe decisões já tomadas → uma `DEC-nnn` por decisão com estado `aprovada` e a fonte (quem/quando).

## Critérios de conclusão

- `AGENTS.md` passa em: cada linha muda um comportamento? há comando de build/test real e executado ao menos uma vez (`[FATO]`)?
- `spec.md` valida contra `platforms/ci/schemas/spec.schema.json`.
- Nada inventado: versões, comandos e caminhos existem.

## Não faça

- Copiar regras genéricas do kit para o repo.
- Fixar metas numéricas (jogadores, latência) sem hipótese e método de medição.
