---
name: postgresql
version: "1.0"
description: PostgreSQL como fonte de verdade — modelagem, migrações Flyway, índices, transações/isolamento, idempotência, backup/restore e diagnóstico (EXPLAIN, locks, bloat). Usar ao criar/alterar schema, investigar lentidão ou planejar persistência.
argument-hint: "[migration | index | tx | backup | diagnose] <contexto>"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# PostgreSQL

Regras: `rules/development/twelve-factor.md` (backing service), `rules/security/secure-development.md` (SQL parametrizado, dados pessoais). Compose local em `kits/docker/`. Nunca rodar comando destrutivo (`DROP`, `TRUNCATE`, `DELETE` sem `WHERE`) sem autorização explícita.

## migration (Flyway)

- Arquivo `V<n>__<slug>.sql` em `src/main/resources/db/migration/`; `n` sequencial; **nunca** editar migração já aplicada (criar `V<n+1>` corretiva).
- Uma mudança lógica por migração. `CREATE INDEX CONCURRENTLY` fora de transação (`-- flyway:executeInTransaction=false`).
- Coluna nova em tabela grande: `ADD COLUMN ... DEFAULT` é rápido (PG ≥11); `NOT NULL` em duas etapas (adicionar → backfill → constraint `NOT VALID` → `VALIDATE`).
- Chaves: `bigint generated always as identity` ou `uuid` (v7 se ordenação importar). `timestamptz`, nunca `timestamp`.
- Dinheiro/moeda de jogo: `bigint` em unidade mínima ou `numeric`; nunca `float`.

## index

- Índice para cada FK e para colunas em `WHERE`/`JOIN`/`ORDER BY` frequentes — provado por `EXPLAIN (ANALYZE, BUFFERS)`, não por intuição.
- Parcial (`WHERE deleted_at IS NULL`) e composto (ordem = seletividade + uso) quando o plano mostrar.
- Não indexar "por precaução": cada índice custa escrita.

## tx (transações)

- Padrão `READ COMMITTED`; operação de economia/inventário → `SELECT ... FOR UPDATE` no aggregate ou `SERIALIZABLE` com retry.
- Idempotência: tabela `processed_commands(command_id pk, result, created_at)`; inserir na mesma transação do efeito.
- Transação curta; nunca I/O externo (HTTP, rede de jogo) dentro dela.
- Deadlock → ordenar locks de forma consistente (por id crescente).

## backup

- `pg_dump -Fc` diário + WAL archiving se RPO < 24h. Testar **restore** (`pg_restore` em banco vazio + smoke query) — backup não testado não existe.
- Dump nunca no repo; local fora do Docker volume.

## diagnose

```sql
EXPLAIN (ANALYZE, BUFFERS) <query>;
SELECT * FROM pg_stat_activity WHERE state <> 'idle';
SELECT * FROM pg_locks l JOIN pg_stat_activity a USING (pid) WHERE NOT granted;
SELECT relname, n_dead_tup, last_autovacuum FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 10;
```
`pg_stat_statements` ligado no compose local para achar queries caras.

## Veredicto

O que foi feito · migração criada (`V<n>`) · prova (`./mvnw flyway:info`/teste de integração) · não verificado · próximo passo.
