# infra-persistence/ — ai-kit persistence — databases

## `skills/`

| Skill | Description |
|---|---|
| `dbeaver` | DBeaver GUI inspection. Use when inspecting a database, exporting test data or drawing an ER diagram. Not for schema changes (skill postgresql). |
| `postgresql` | PostgreSQL persistence rules. Use when changing a schema, migration or index, running EXPLAIN, or diagnosing locks. Not for cache data (skill redis). |
| `redis` | Redis ephemeral-data rules. Use when designing cache keys/TTL, rate limits, pub/sub or short locks. Not for durable data (skill postgresql). |

Manifests: `.devin-plugin/plugin.json` (Devin) · `.claude-plugin/plugin.json` (Claude) · `plugin.json` (Codex).
