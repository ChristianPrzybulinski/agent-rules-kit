---
name: simplicity
description: YAGNI ladder for the smallest change. Use when choosing a dependency, reviewing an oversized PR or adding an abstraction. Not for test gates (skill testing).
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
  - edit
---

# Simplicity

## 1. Read the whole touched flow

Locate callers, neighboring implementations and existing dependencies before selecting a solution. The ladder reduces the implementation, not the investigation.

## 2. Stop at the first sufficient rung

1. Does the requested behavior need to exist now?
2. Does the repository already contain the helper, type or pattern?
3. Does the standard library solve it?
4. Does the database, engine or platform provide it natively?
5. Does an already-installed dependency solve it?
6. Does the correct implementation fit clearly in one line?
7. Only then write the minimum new code.

Choose the higher rung when two work; never trade correctness at an edge case for fewer characters.

## 3. Search before adding a utility or dependency

- Search Maven Central, Godot Asset Library or `gh search code` before writing a reusable utility.
- Before adding a dependency, verify it is not already present/transitive, matches the runtime, has a compatible published version, is at least seven days old and has zero critical/high CVEs.
- Prefer adoption over maintaining a local clone of ecosystem behavior.

## 4. Reject speculative structure

Do not add a one-implementation interface, one-product factory, future-only configuration or unrequested scaffolding. A port is justified only by external I/O, a real planned swap or a domain boundary.

## 5. Protect non-negotiable behavior

Never simplify trust-boundary validation, data-loss prevention, security/authorization, accessibility, an explicit user requirement, or domain integrity for money/inventory/reward/battle.

For a deliberate ceiling, add `// simplified: <ceiling>; <when/how to evolve>` and create `DEBT-xxx` when the roadmap reaches it.

## 6. Report the ceiling

Use `[code] → skipped: X; add when Y.` Delete explanation that exceeds the simple change unless the user requested a report.

Done when: the solution stops at the earliest safe rung, adds no speculative dependency/abstraction, and records any deliberate ceiling with its evolution trigger.
