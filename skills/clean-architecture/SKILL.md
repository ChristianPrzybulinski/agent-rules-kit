---
name: clean-architecture
description: Clean Architecture layer and port placement. Use when defining layers, ports or where a class lives. Not for pattern choice (skill ddd-and-patterns).
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - edit
---

# Clean Architecture

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

## 5. Verify the boundary

- Domain tests run without database, network, UI or framework context.
- Use fakes at ports; do not mock entities.
- Inspect imports or run the project's architecture gate before closing.

Done when: every dependency points inward, validation/error translation occurs at the edge, and each port names its I/O, swap or domain-boundary reason.
