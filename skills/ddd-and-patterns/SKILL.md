---
name: ddd-and-patterns
description: Tactical DDD and pattern selection. Use when defining an aggregate or choosing a design pattern. Not for layer placement (skill clean-architecture).
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - edit
---

# Tactical DDD and Patterns

## 1. Name the present problem

State the invariant, lifecycle, variation or coordination problem before selecting a pattern. A non-obvious pattern needs one recorded reason in code or a DEC; popularity and hypothetical reuse are not reasons.

## 2. Select a tactical building block

| Building block | Use when |
|---|---|
| Value Object | immutable concept is defined by validated attributes |
| Entity | identity persists while attributes change |
| Aggregate | invariants must succeed together in one transaction |
| Domain Event | a completed domain fact must notify another module |
| Repository | a whole aggregate crosses persistence |
| Domain Service | a domain rule belongs to no single entity/value object |

Aggregate boundaries follow transaction invariants, not table or screen boundaries.

## 3. Select the smallest pattern

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

Do not introduce Event Sourcing, CQRS or microservices without a measured need. Tactical aggregates, value objects and events do not require those architectures.

## 4. Block accidental patterns

Reject mutable global singletons, Active Record in the domain, anemic entities, ownerless utility classes and inheritance used only for code reuse.

Done when: the chosen building block or pattern solves a named current problem, its rejected simpler option is understood, and no speculative architecture was added.
