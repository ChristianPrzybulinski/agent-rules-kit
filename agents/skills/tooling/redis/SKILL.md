---
name: redis
version: "1.0"
description: Redis como cache/efêmero — quando usar (e quando não), chaves com TTL, pub/sub para presença, rate limit, locks curtos; nunca fonte de verdade de inventário, progressão ou economia. Usar ao propor cache, sessão, fila leve ou coordenação.
argument-hint: "[justify | cache | ratelimit | pubsub | lock] <contexto>"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - exec
---

# Redis

Decisão do produto (`[DECISÃO]`): Redis disponível **para necessidades justificadas**; **nunca** fonte de verdade de inventário, progressão ou economia (isso é PostgreSQL). Compose em `platforms/kits/docker/`.

## justify (antes de usar)

Responda por escrito na FEAT/DEC:
1. Que problema medido o Postgres não resolve? (latência p95, contenção, volume) — sem medição → `[HIPÓTESE]`, comece **sem** Redis.
2. O dado pode ser perdido a qualquer momento sem inconsistência? Se não → não é Redis.
3. Como o sistema se comporta com Redis fora? Deve degradar, não quebrar.

## Usos aceitos

| Uso | Estrutura | TTL | Observação |
|---|---|---|---|
| Cache de leitura (conteúdo estático, perfil) | `STRING`/`HASH` `cache:<tipo>:<id>` | sim, sempre | invalidar na escrita; cache-aside |
| Presença/online | `SET` por mapa + `EXPIRE` renovado por heartbeat | 30-60 s | fonte é a conexão, Redis é reflexo |
| Rate limit | `INCR` + `EXPIRE` por `<ator>:<ação>:<janela>` | janela | sliding window se precisar precisão |
| Pub/sub entre instâncias do servidor | canal por mapa/região | — | só se >1 processo; senão in-memory |
| Lock curto | `SET key val NX PX <ms>` + release por script Lua comparando `val` | ≤ 5 s | nunca para invariante de economia (isso é `FOR UPDATE` no PG) |
| Fila leve | `XADD`/Streams | — | reavaliar se precisar de garantia forte |

## Regras

- Toda chave tem prefixo `<app>:<tipo>:` e TTL (exceto pub/sub). Sem TTL = vazamento.
- Serialização: JSON pequeno ou `HASH`; nunca objeto Java serializado.
- Config `maxmemory-policy allkeys-lru` (cache) ou `noeviction` + alerta (se algo não puder evaporar — então questione se é Redis).
- Cliente: Lettuce (Spring Data Redis padrão); timeout curto; circuit breaker (Resilience4j) → fallback ao PG.

## Veredicto

Uso proposto · justificativa (medida ou `[HIPÓTESE]`) · comportamento sem Redis · chaves/TTL · não verificado · próximo passo.
