---
name: clean-architecture
version: "1.0"
description: Clean Architecture details — layers, dependency rule, ports/adapters, DTOs, exceptions. Use when creating a module, a layer or deciding where a class lives. Do not use for choosing a design pattern (skill ddd-and-patterns) or naming detail (skill clean-code).
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
---

# Clean Architecture

## Layers (outside in)

1. Frameworks & Drivers (UI, DB, external APIs, libraries).
2. Interface Adapters (controllers, presenters, gateways, DTOs).
3. Use Cases (application rules, orchestration).
4. Entities (business rules, pure domain).

## Dependency Rule

- Dependencies **always point inward**.
- Inner layers do not know outer layers.
- Use interfaces (ports) to invert dependencies **where there is something to invert** (below).

## Pragmatism — when a port is justified

| Situation | Port? |
|---|---|
| Domain needs database, network, clock, RNG, file, queue | **Yes** — external I/O; it's what gets replaced by a fake in tests |
| Real alternative implementations expected (Postgres today, another tomorrow; optional Redis) | Yes |
| Domain boundary consumed by another module | Yes, at the boundary; not on every internal class |
| Internal service/policy with one implementation (`DamageFormula`, `EvolutionPolicy`) | **No** — concrete class, tested directly |
| "Might be useful someday" | No — YAGNI (skill `simplicity`) |

A port with no second implementation **and** no I/O is ceremony: remove it. Empty layers (an `application` package that only forwards) too.

Fewer files wins: group by use case/aggregate, not by technical type (`services/`, `impl/`, `interfaces/`).

## Frameworks are details

- The domain and use cases must not depend on Spring, Hibernate, Godot nodes, specific GDScript, etc.
- Isolate adapters to swap frameworks without touching the core.

## DTOs and boundaries

- Use DTOs at the edge between layers. Never pass entities directly to the UI/DB without adaptation.
- Keep DTOs lean and immutable when possible.

## Testability

- Business rules must be testable without a database, network or UI.
- Use mocks/fakes for ports, never for entities.

## Exceptions

- Domain exceptions (inner layer) are different from infrastructure errors (outer layer).
- Convert external exceptions into domain exceptions near the boundary.
