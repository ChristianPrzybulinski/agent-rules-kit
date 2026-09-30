---
name: sdd-plan
version: "1.0"
description: Etapa 5 do SDD — plano técnico de uma FEAT clarificada e auditada - módulos tocados, modelo de domínio, contrato, persistência/migração, feature flag, estratégia de testes, riscos; cria DEC-nnn para decisões com alternativa rejeitada. Status vira planejada. Usar após sdd-audit, antes de sdd-tasks.
argument-hint: "FEAT-nnn [restrições técnicas]"
triggers:
  - user
allowed-tools:
  - read
  - glob
  - grep
  - edit
  - write
  - exec
---

# SDD 5 — Plan

Pré-requisito: `status: clarificada`, audit sem ✗ de segurança. Referências: `agents/rules/architecture/*`, `agents/rules/java/*`, `agents/rules/godot/*`, `AGENTS.md` do repo, `docs/spec/decisions/`.

## Etapas

1. Ler código existente das áreas tocadas (não presuma estrutura). Listar arquivos/módulos reais.
2. Escrever seção **Plano** na FEAT:
   - **Domínio**: aggregates/VOs/eventos novos ou alterados; invariantes que o servidor protege.
   - **Fronteiras**: o que fica em cliente (apresentação/intenção) vs servidor (validação/resultado) vs protocolo.
   - **Contrato**: mensagens/endpoints novos ou alterados, com exemplo mínimo; compatível ou incompatível (`protocol_version`).
   - **Persistência**: tabelas/colunas, migração `V<n>__slug.sql`, índices, transação, idempotency key se aplicável.
   - **Feature flag**: nome, default, comportamento desligado — ou "não precisa" com motivo.
   - **Testes**: por critério de aceite → tipo de teste e onde vive. Domínio: casos em tabela.
   - **Observabilidade**: logs/métricas que provam funcionamento.
   - **Riscos e hipóteses**: cada `[HIPÓTESE]` com como/quando validar.
   - **Dependências/bloqueios**: outras FEATs, ferramentas, decisões pendentes.
3. Toda escolha com alternativa razoável rejeitada → `DEC-nnn-slug.md` (template `decision.md`), estado `proposta`; referenciar na FEAT. Decisão já aprovada pelo produto → `aprovada` com fonte.
4. Plano viola regra do kit/repo → não planeje o contorno: registre `[BLOQUEIO]` ou proponha `DEC` explícita.
5. `status: planejada`; *Histórico* atualizado; `sdd-analyze FEAT-nnn` deve passar sem crítica/alta.

## Critérios de conclusão

- Cada critério de aceite tem teste planejado.
- Nenhuma decisão técnica relevante sem `DEC` ou sem justificativa de 1 linha.
- Não introduz camada/infra (fila, cache, serviço) sem necessidade demonstrada no plano.
