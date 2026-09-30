---
name: [nome-da-pasta]
version: "1.0"
description: "[O que faz em 1 frase]. Usar quando [gatilho concreto]. Não usar para [caso vizinho que confunde]."
argument-hint: "[argumento esperado | vazio]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# [Nome]

[Uma frase: o resultado que esta skill produz e o que ela NÃO faz.]

## 1. [Etapa — verbo no infinitivo]

- [ação observável; comando quando houver]

## 2. [Etapa]

## 3. Fechar

- [artefato produzido: caminho/template]
- [verificação: comando + saída esperada]

## Regras

- [limite de atuação: o que a skill nunca faz]

<!-- Limite: 80 linhas. Regras de domínio ficam em rules/ e são referenciadas, não copiadas. -->
