---
description: Tactical DDD and a design patterns catalog with "when to use / when not". Load when modeling a domain, choosing a pattern or reviewing a module's architecture.
trigger: model_decision
---

# Tactical DDD and patterns

A pattern is justified by a present problem, not by popularity. Each non-obvious use → 1 line of "why" in the code or an ADR.

## DDD — what to use

| Block | Use when | Example |
|---|---|---|
| Value Object | concept defined by its attributes, immutable | `Money`, `Position`, `Hp` — `record` with constructor validation |
| Entity | identity persists over time | `Player`, `Creature` |
| Aggregate | invariants must be guaranteed together in one transaction | `Inventory` (items + capacity), `BattleInstance` (turns + participants) |
| Domain Event | something happened and other modules react | `BattleEnded`, `ItemAcquired` |
| Repository | persist/retrieve a whole aggregate | `PlayerRepository` (port in `application`, JPA impl in `adapter`) |
| Domain Service | rule that doesn't belong to an entity | `DamageCalculator` |

Do not use: formal strategic DDD (context maps, per-team ubiquitous language) with 1 dev; Event Sourcing without a need to rebuild history; full CQRS before there are measured distinct read/write profiles.

## Catalog — when yes / when no

| Pattern | Yes | No |
|---|---|---|
| Ports & Adapters | always at the domain↔infra boundary | — |
| Command | user actions validated/queued/audited (`MoveCommand`, `AttackCommand`) | simple CRUD |
| State Machine | states with explicit transitions (battle turn, connection, quest) | 2 boolean states |
| Strategy | algorithm variations chosen at runtime (attack effect, per-type damage calculation) | 1 implementation |
| Specification | combinable, named validation rules (`CanEvolve`, `CanTrade`) | a single `if` |
| Transactional Outbox | event must go out **if and only if** the transaction committed (reward, trade) | informational event without consequence |
| Idempotency Key | operation may be resent (network, retry) and must not duplicate its effect | read |
| Factory | creation with invariants or multiple steps | a constructor suffices |
| Observer/Signals | decouple who emits from who reacts (Godot: signals; Java: Domain Events) | direct call is clear and local |
| Object Pool | measured frequent, expensive creation (projectiles, particles) | premature optimization |
| Repository | aggregate access | static lookup table |

## Anti-patterns to block in review

- Singleton for mutable game state (Godot: autoload becoming a "god object"; Java: mutable `static`).
- Active Record in the domain (entity that saves itself).
- Anemic Domain: entity with only getters/setters and rules in the "service".
- Generic Utils/Helpers growing without an owner.
- Inheritance for code reuse (use composition).
