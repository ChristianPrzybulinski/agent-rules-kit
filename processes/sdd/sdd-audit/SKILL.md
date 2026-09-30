---
name: sdd-audit
version: "1.0"
description: Etapa 4 do SDD — auditoria de qualidade da spec com checklist - testabilidade, completude, segurança, dados, erros, compatibilidade, observabilidade. Gera lista de gaps a corrigir antes do plano. Usar quando a FEAT está clarificada.
argument-hint: "FEAT-nnn"
triggers:
  - user
  - model
allowed-tools:
  - read
  - glob
  - grep
  - write
---

# SDD 4 — Audit (checklist)

Equivalente ao `checklist` do spec-kit. Produz `docs/spec/features/FEAT-nnn.checklist.md` (ou seção *Auditoria* na FEAT, conforme o projeto) com itens ✓/✗/n.a. e justificativa.

## Checklist

**Testabilidade**
- [ ] Cada critério tem caminho feliz e triste.
- [ ] Cada critério indica o tipo de teste que o prova (unit/integração/contrato/e2e).
- [ ] Dados de teste descritos sem dados pessoais reais.

**Completude**
- [ ] Estados de erro definidos (entrada inválida, recurso ausente, conflito, timeout, sem permissão).
- [ ] Comportamento em reconexão/retentativa definido, se envolve rede.
- [ ] Limites (tamanho, frequência, quantidade) numéricos ou `[HIPÓTESE]`.

**Segurança e integridade**
- [ ] Quem pode executar (authz por ação e entidade).
- [ ] O que o servidor valida vs. o que confia do cliente (nada).
- [ ] Operação com dinheiro/inventário/recompensa → idempotência e transação descritas.
- [ ] Dados pessoais envolvidos listados; retenção definida.

**Dados e compatibilidade**
- [ ] Mudança de schema → migração mencionada; dados existentes tratados.
- [ ] Mudança de contrato → compatível/incompatível decidido; `protocol_version` impactado?
- [ ] Windows e macOS considerados, se toca cliente.

**Operação**
- [ ] O que logar/medir para saber que funciona em produção.
- [ ] Feature flag necessária? nome e comportamento desligado.

**Documentação**
- [ ] Docs a atualizar listados (README, CHANGELOG, protocolo, glossário).

## Saída

Itens ✗ viram lista de gaps com ação (voltar a `clarify`, editar spec, ou `[HIPÓTESE]` explícita). Gap de segurança/integridade ✗ → **bloqueia** `plan`.
