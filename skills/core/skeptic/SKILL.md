---
name: skeptic
version: "1.0"
description: Verificação adversarial de uma afirmação (minha, do usuário ou de doc). Busca evidência contrária primeiro, depois favorável, e emite veredicto com confiança. Usar quando algo "parece certo" mas não foi provado, ou quando o usuário sugere uma solução.
argument-hint: "[afirmação a verificar — padrão: última afirmação relevante]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
  - web_search
  - webfetch
---

# Skeptic — verificação adversarial

Objetivo: substituir "parece certo" por evidência. Nunca concluir "verdadeiro" sem fonte verificável; nunca concluir "falso" sem tentar sustentar a afirmação.

## 1. Fixar a afirmação

- Use `$ARGUMENTS` se fornecido; senão, a última afirmação factual ou proposta de solução na conversa.
- Reescreva-a em uma frase falsificável ("X faz Y em Z"). Se não for falsificável, diga isso e pare.

## 2. Classificar e escolher fontes

| Tipo de afirmação | Fonte primária | Fonte secundária |
|---|---|---|
| Comportamento do código do repo | ler o arquivo + rodar teste/comando | git log/blame |
| API, flag, versão de lib/framework | doc oficial da versão instalada (`pom.xml`, `project.godot`, lockfile) | changelog/release notes |
| Melhor abordagem / arquitetura | 2+ alternativas concretas com trade-offs medidos no contexto do repo | referência reconhecida (livro, doc oficial) |
| Fato externo | fonte primária (site oficial, RFC, spec) | 2 fontes independentes |

## 3. Buscar evidência CONTRÁRIA primeiro

- Procure ativamente o que refutaria a afirmação: teste que falha, doc que diz o oposto, caso de borda, versão diferente.
- Se a afirmação é uma solução proposta, liste 1-2 alternativas e o que elas fazem melhor.
- Registre cada achado com fonte (caminho:linha, URL, saída de comando).

## 4. Buscar evidência FAVORÁVEL

- Só depois do passo 3. Mesma exigência de fonte.

## 5. Veredicto

Formato obrigatório (curto):

```
Afirmação: <frase falsificável>
Veredicto: CONFIRMADA | REFUTADA | PARCIAL | INDETERMINADA
Confiança: NN%  (≥98% exigido para prosseguir sem ressalva)
Contra: - <evidência + fonte>
A favor: - <evidência + fonte>
Alternativas (se solução): - <opção> — <trade-off>
Recomendação: <o que fazer agora; se <98%, o que falta para chegar lá>
```

## Regras

- Não conte "a doc diz" sem citar a versão e o trecho.
- Não conte lembrança de treinamento como evidência.
- Se a verificação exige rodar algo destrutivo, pare e peça autorização.
- Se após esforço razoável nada decide, INDETERMINADA com o próximo teste concreto que decidiria.
