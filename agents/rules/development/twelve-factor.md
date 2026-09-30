---
description: Twelve-Factor App aplicado a serviços Java e ferramentas locais — config por ambiente, processos stateless, logs como stream, paridade dev/prod. Carregar ao configurar aplicação, Docker, variáveis ou deploy.
trigger: model_decision
---

# Twelve-Factor (o que vale aqui)

| Fator | Regra prática |
|---|---|
| I. Codebase | 1 repo por app (ou monorepo com módulos); mesma base em todos os ambientes. |
| II. Dependências | Declaradas no `pom.xml`/`project.godot`; sem lib instalada "na máquina". Versões fixas, sem ranges. |
| III. Config | Tudo que varia por ambiente vem de variável de ambiente. `application.yml` só tem defaults seguros e `${VAR}`. `.env.example` versionado; `.env` nunca. |
| IV. Backing services | Postgres, Redis, filas = recursos anexados por URL. Trocar de local para nuvem = mudar env, não código. |
| V. Build/release/run | Artefato imutável (jar, export Godot). Config injetada no run. Nunca editar artefato em produção. |
| VI. Processos | Stateless. Sessão e estado de jogo persistem em Postgres (fonte da verdade) ou Redis (cache/efêmero, nunca fonte da verdade de inventário/economia). |
| VII. Port binding | App expõe porta própria; sem depender de container de servlet externo. |
| VIII. Concorrência | Escalar por processo; JVM: virtual threads para I/O, pool fixo para CPU. |
| IX. Descartabilidade | Start rápido, shutdown gracioso (`SIGTERM` → fecha conexões, termina transações). |
| X. Paridade dev/prod | Mesmo Postgres/Redis (versão major) local via Compose e em produção. Sem H2 "só para testes". |
| XI. Logs | Stream em stdout, JSON estruturado, com `correlation_id`. Sem arquivo de log gerenciado pela app. |
| XII. Admin | Migrações (Flyway) e tarefas administrativas como comandos versionados, rodando com a mesma config. |

## Condição → ação

- Novo parâmetro configurável → `@ConfigurationProperties` + entrada em `.env.example` com comentário + default seguro.
- Segredo → env/keychain; nunca em yml, código ou log.
- Nova dependência externa (banco, fila, API) → URL/credencial por env + serviço no `docker-compose.yml`.
