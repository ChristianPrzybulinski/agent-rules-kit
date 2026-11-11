# architect-core/ — ai-kit architecture — system design standards

## `skills/`

| Skill | Description |
|---|---|
| `architecture` | Layers, ports, DDD blocks and pattern choice. Use when placing a class, defining an aggregate or picking a pattern. Not for contracts (skill protocol-contract). |
| `grilling` | Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases. |
| `protocol-contract` | Client↔server contracts. Use when adding a message or field, changing a payload or fixing a client/server mismatch. Not for transport choice (skill sdd-plan). |
## `templates/`

- `doc-contract-message.md`


## `evals/`

- `architecture-idempotent-import`
- `architecture-illegal-states`
- `architecture-pure-battle-core`
- `protocol-contract-field-owned-by-other-feat`
- `protocol-contract-no-transport-dec`
- `protocol-contract-required-field-bumps-version`

Manifests: `.devin-plugin/plugin.json` (Devin) · `.claude-plugin/plugin.json` (Claude) · `plugin.json` (Codex).
