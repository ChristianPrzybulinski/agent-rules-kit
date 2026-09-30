---
description: Escada da simplicidade (YAGNI pragmático) — quando não escrever código, quando um port/interface se justifica, como marcar simplificações deliberadas e como reportar o que foi pulado. Carregar ao desenhar solução, revisar PR "grande demais", escolher dependência ou decidir se um teste é necessário; o resumo já está no AGENTS.md.
trigger: model_decision
---

# Simplicidade

O melhor código é o que não foi escrito. Lazy = eficiente, não descuidado. A escada encurta a **solução**, nunca a **leitura**: entenda o fluxo inteiro (todos os arquivos que a mudança toca) antes de escolher o degrau.

## A escada — pare no primeiro degrau que segura

1. **Precisa existir?** Necessidade especulativa → não faça; diga em uma linha.
2. **Já existe no repositório?** Helper, tipo, padrão a três arquivos de distância → reuse. Reimplementar o vizinho é o erro mais comum.
3. **Stdlib resolve?** Use.
4. **Recurso nativo da plataforma?** Constraint no banco em vez de código; sinal nativo do Godot em vez de bus próprio; `record` em vez de builder.
5. **Dependência já instalada resolve?** Use. Nunca adicione uma nova para o que cabe em poucas linhas.
6. **Cabe em uma linha?** Uma linha.
7. **Só então:** o mínimo que funciona.

Dois degraus funcionam → o mais alto. Duas opções do mesmo tamanho → a correta nos casos de borda (menos código, não algoritmo mais frágil).

## Regras

- Sem abstração não pedida: interface com uma implementação, factory de um produto, config para valor que nunca muda, scaffolding "para depois".
- **Exceção que justifica interface (port)**: I/O externo (banco, rede, relógio, RNG, arquivo), troca real prevista entre implementações, ou fronteira do domínio que precisa ser testada sem infraestrutura. Fora disso, classe concreta.
- Menos arquivos vence. Deletar vence adicionar. Chato vence esperto — esperto é o que alguém decifra às 3h da manhã.
- Bug = causa raiz. Antes de editar, `grep` todos os chamadores; a correção no ponto comum é o menor diff **e** o correto.
- Pedido complexo → entregue a versão simples e questione no mesmo turno: "Fiz X; Y cobre. Precisa do X completo? Diga."
- Simplificação deliberada com teto conhecido (lock global, varredura O(n²), heurística) → comentário `// simplificado: <teto>; <quando/como evoluir>`. Vira `DEBT-xxx` se o teto estiver no caminho do roadmap.

## Nunca simplifique

Validação na borda de confiança · tratamento de erro que evita perda de dado · segurança e autorização · acessibilidade básica · o que o usuário pediu explicitamente (insistiu → construa, sem rediscutir) · o **domínio** (dinheiro, inventário, recompensa, batalha): lá valem os gates de `rules/development/testing.md` integralmente.

## Testes sob a escada

- Fora do domínio: lógica não trivial deixa **um** check executável que falha se quebrar (um `test_*`/`@Test` pequeno). Sem suíte por função, sem fixture antecipada. Trivial (getter, mapeamento 1:1, one-liner) não se testa.
- Dentro do domínio: a escada não se aplica aos testes.

## Saída

Padrão: `[código] → pulado: X; adicionar quando Y.` Se a explicação ficou maior que o código, apague a explicação. Explicação pedida explicitamente (relatório, walkthrough) não é dívida — entregue inteira.
