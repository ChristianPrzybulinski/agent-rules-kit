---
description: Search order and verification checks before writing a reusable utility or adding a dependency.
kind: detail
---

# Dependency search

## Search before writing a utility

- Search Maven Central, Godot Asset Library or `gh search code` before writing a reusable utility.
- Prefer adoption over maintaining a local clone of ecosystem behavior.

## Check before adding a dependency

Verify each of the five checks before the dependency enters the manifest:

1. it is not already present or transitive;
2. it matches the runtime;
3. it has a compatible published version;
4. it is at least seven days old;
5. it has zero critical/high CVEs.
