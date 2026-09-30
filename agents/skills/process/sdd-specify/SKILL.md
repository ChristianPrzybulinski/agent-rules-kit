---
name: sdd-specify
version: "1.0"
description: Etapa 1 do SDD — transforma uma descrição de funcionalidade em FEAT-nnn (o quê e porquê, sem como) e nos REQ-F/REQ-NF ligados, com critérios de aceite testáveis. Usar ao iniciar qualquer funcionalidade nova.
argument-hint: "<descrição da funcionalidade em linguagem natural>"
triggers:
  - user
allowed-tools:
  - read
  - glob
  - grep
  - write
  - exec
---

# SDD 1 — Specify

Templates: `agents/templates/spec-feature.md`, `requirement-functional.md`, `requirement-non-functional.md`.

## Etapas

1. Próximo número: `ls docs/spec/features | sort | tail -1`. Nunca reutilize.
2. Ler `docs/spec/spec.md` (escopo, glossário) e features existentes: a funcionalidade já existe, colide ou depende de outra? Registre em *Relações*.
3. Escrever `FEAT-nnn-slug.md`:
   - **Problema/valor** para o jogador/usuário (porquê). 
   - **Escopo** e **Fora de escopo** explícitos.
   - **Critérios de aceite** no formato Given/When/Then, cada um verificável por teste automatizado ou passo reproduzível. Mínimo: 1 caminho feliz, 1 triste.
   - **Requisitos ligados**: criar `REQ-F-*` (comportamento) e `REQ-NF-*` (desempenho, segurança, compatibilidade) novos ou referenciar existentes. Cada requisito = 1 arquivo, 1 frase testável.
   - **Perguntas abertas** marcadas `[NEEDS CLARIFICATION: ...]` — máximo 5; se passar disso, o pedido está grande demais: proponha dividir.
   - **Sem** decisões técnicas (framework, tabela, mensagem). Isso é `sdd-plan`.
4. Frontmatter: `id`, `title`, `status: proposta`, `requirements: [...]`, `flag: null`, `card: null`, `created`.
5. Atualizar índice em `spec.md`.
6. Validar: `platforms/tools/check.sh --spec docs/spec` (schemas).

## Critérios de conclusão

- Todo critério de aceite responde "que teste prova isso?".
- Nenhum requisito órfão (sem FEAT) nem FEAT sem requisito.
- Afirmações classificadas (`[FATO]`/`[HIPÓTESE]`/...).
