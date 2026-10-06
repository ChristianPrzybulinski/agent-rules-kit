---
name: architecture
description: Layers, ports, DDD blocks and pattern choice. Use when placing a class, defining an aggregate or picking a pattern. Not for contracts (skill protocol-contract).
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - edit
---

# Architecture

## 1. Map the dependency direction

Classify touched code as entity/domain, use case/application, interface adapter, or framework/driver. Dependencies point inward; domain and application code import no Spring, Hibernate, Godot node, database or transport type.

## 2. Place boundaries

- Validate external input at the adapter boundary, then trust the typed interior.
- Pass DTOs across layers; do not expose domain entities directly to UI, persistence or transport code.
- Translate infrastructure failures at the boundary while preserving a specific domain/application error.

## 3. Justify each port

Create a port only for:

1. external I/O such as database, network, clock, RNG, file or queue;
2. a real planned implementation swap; or
3. a domain boundary consumed by another module.

A single internal policy with no I/O stays concrete. Remove ports with neither a second implementation nor a boundary.

## 4. Structure by behavior

- Group files by use case or aggregate, not generic `services/`, `interfaces/` and `impl/` buckets.
- Keep wiring and framework annotations in outer adapters/bootstrap.
- Reject empty layers that only forward calls; fewer files and inward dependencies win.

## 5. Name the present problem, then pick the smallest block

State the invariant, lifecycle, variation or coordination problem before selecting a building block or pattern. A non-obvious pattern needs one recorded reason in code or a DEC; popularity and hypothetical reuse are not reasons. Pick the smallest building block or pattern that fits from `references/pattern-catalog.md`. Aggregate boundaries follow transaction invariants, not table or screen boundaries.

## 6. Block accidental patterns and speculative architectures

Reject mutable global singletons, Active Record in the domain, anemic entities, ownerless utility classes and inheritance used only for code reuse. Do not introduce Event Sourcing, CQRS or microservices without a measured need; tactical aggregates, value objects and events do not require those architectures.

## 7. Verify the boundary

- Domain tests run without database, network, UI or framework context.
- Use fakes at ports; do not mock entities.
- Inspect imports or run the project's architecture gate before closing.

Done when: every dependency points inward, validation/error translation occurs at the edge, each port names its I/O, swap or domain-boundary reason, and the chosen building block or pattern solves a named current problem with its rejected simpler option understood and no speculative architecture added.
