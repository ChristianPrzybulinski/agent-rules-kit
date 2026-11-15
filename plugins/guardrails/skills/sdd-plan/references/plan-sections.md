---
description: What each FEAT Plan section holds, the "— why" line for a section that does not apply, and an example. Load when writing a FEAT's Plan.
kind: detail
---

# Plan sections

`sdd-plan` writes one `### <section>` per name in the project's `plan_sections` (default all nine, `Risks` and `Tests` always on), in the order below. A section in the list that does not apply holds one line `— <why>`; a section the project turned off is absent. The Plan is the design: every choice the task rows need is made here, and a row's Task cell points to `Plan § <section>`.

| Section | Holds |
|---|---|
| Design | domain aggregates, value objects and events, the invariants they protect; client, server, protocol and adapter boundaries; the rooted files or modules each change lands in and the `spec.md` § Architecture areas they belong to |
| Contract | each changed message, endpoint, schema or content file with its compatibility and protocol-version effect, and the four checks of `contract.md` |
| Data | tables and columns, the migration `V<n>__slug.sql`, indexes, transaction boundary and idempotency, cache keys and their expiry |
| UI | each screen or state, the REQ mock it matches, input and feedback, what the player or user sees on failure |
| Flag | the feature flag name, its default and the behavior with it off, or why none is needed |
| Tests | each acceptance criterion's test type and rooted location; the failing domain test that starts each business rule; fixtures and their source |
| Observability | logs, metrics and traces, and the question each one answers |
| Risks | at most three load-bearing hypotheses, each `Fails if <condition>` with its cheapest test (one that needs code becomes an `sdd-spike`); each external API with its exact signature and the source read this session |
| Dependencies | the FEATs in `depends_on` and what this one reads from each, external services, approvals and blockers |

A decision record holds a choice with a rejected alternative that outlives the FEAT; the Plan section cites its id and keeps one line. A choice that matters only inside the delivery stays in its section, with the rejected alternative in one line.

## Example

```markdown
## Plan

### Design

`server/battle/TurnResolver.java` (area battle) resolves both moves of a turn; invariant: a fainted creature never acts.

### Contract

`protocol/battle/turn-result.json` gains `order: [string]`, the public ids of the acting creatures (contract.md 1).

### Data

— no storage: turns live in the match aggregate's memory.

### Flag

— no flag: the server sends `order` only to clients at protocol version 7.

### Tests

CA-1 unit `server/battle/TurnResolverTest.java`; CA-2 contract `protocol/battle/examples/turn-result.json`.

### Risks

- Fails if two equal speeds resolve in a different order on client and server; cheapest test: a seeded unit test.
```
