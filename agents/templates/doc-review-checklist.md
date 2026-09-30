# Checklist de revisão — PR #[n] — `FEAT-xxx`

Marque só o que foi **observado**. Item não aplicável: `n/a`. Item não verificado: deixe vazio e diga por quê no final.

## Escopo
- [ ] PR faz uma coisa; título Conventional Commit; corpo linka FEAT/REQ/DEC.
- [ ] Nada fora do escopo da FEAT (tangentes viraram issue/DEBT).

## Correção
- [ ] Cada CA da FEAT tem teste nomeado; caminho triste coberto.
- [ ] Domínio: JaCoCo 100% + PITest ≥80% verdes (saída no PR).
- [ ] Efeito em inventário/economia/recompensa: teste de idempotência e concorrência.
- [ ] Contrato alterado → `protocol_version` e fixtures atualizados nos dois lados.

## Arquitetura
- [ ] Dependências apontam para dentro; domínio sem framework.
- [ ] Servidor valida tudo que altera estado; cliente só pré-valida UX.
- [ ] Sem padrão novo sem problema presente; DEC se houve trade-off.

## Segurança
- [ ] Sem segredo/dado pessoal; `vuln-scan` OK; input validado na borda; erro não vaza interno.
- [ ] Log sem senha/token; autorização por ação/entidade nos endpoints tocados.

## Docs
- [ ] CHANGELOG `Unreleased`; README se comando mudou; Javadoc/docstring em API pública nova.
- [ ] Status da FEAT e `updated` atualizados; DEBT/flag registrados se incompleto.

## Ao receber comentários de revisão (autor)
- [ ] Cada comentário verificado no código antes de aplicar — revisor também erra; discordância vai com evidência, não com "ok".
- [ ] Comentário que revela lacuna na FEAT/REQ → corrigir a spec, não só o código.
- [ ] Nenhuma mudança fora do comentário "aproveitando"; segue para follow-up.

## Não verificado
- [...]
