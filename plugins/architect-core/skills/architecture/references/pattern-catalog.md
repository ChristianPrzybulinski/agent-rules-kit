---
description: Tactical DDD building blocks and design patterns mapped to the present problem each one solves.
kind: detail
---

# Pattern catalog

## Tactical building blocks

| Building block | Use when |
|---|---|
| Value Object | immutable concept is defined by validated attributes |
| Entity | identity persists while attributes change |
| Aggregate | invariants must succeed together in one transaction |
| Domain Event | a completed domain fact must notify another module |
| Repository | a whole aggregate crosses persistence |
| Domain Service | a domain rule belongs to no single entity/value object |

## Patterns

| Pattern | Present problem |
|---|---|
| Command | action must be validated, queued or audited |
| State Machine | named states have constrained transitions |
| Strategy | multiple algorithms are selected at runtime |
| Specification | validation rules must be named and composed |
| Transactional Outbox | an event must publish iff its transaction commits |
| Idempotency Key | a retried command must not repeat its effect |
| Factory | creation has invariants or multiple steps |
| Observer/signal | emitter and responders must vary independently |
| Object Pool | profiling proves frequent expensive allocation |
