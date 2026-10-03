# architect-core/ — ai-kit architecture — system design standards

## `skills/`

| Skill | Description |
|---|---|
| `clean-architecture` | Clean Architecture layer and port placement. Use when defining layers, ports or where a class lives. Not for pattern choice (skill ddd-and-patterns). |
| `ddd-and-patterns` | Tactical DDD and pattern selection. Use when defining an aggregate or choosing a design pattern. Not for layer placement (skill clean-architecture). |
| `grilling` | Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases. |
| `protocol-contract` | Client↔server contracts. Use when adding a message or field, changing a payload or fixing a client/server mismatch. Not for transport choice (skill sdd-plan). |
## `templates/`

- `doc-contract-message.md`


Manifests: `.devin-plugin/plugin.json` (Devin) · `.claude-plugin/plugin.json` (Claude) · `plugin.json` (Codex).
