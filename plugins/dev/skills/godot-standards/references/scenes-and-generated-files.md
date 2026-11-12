---
description: Godot 4 generated files under version control - commit *.uid and *.import, never .godot/, .tscn conflict handling and scene ownership rules.
kind: fact
verified: "2026-10-06"
sources:
  - https://godotengine.org/article/uid-changes-coming-to-godot-4-4/
  - https://docs.godotengine.org/en/stable/tutorials/best_practices/version_control_systems.html
---

# Godot 4 - scenes and generated files

## What to commit

- Commit `*.uid`: since Godot 4.4 the editor writes one next to every script and other non-resource file; a missing or stale UID breaks `uid://` references.
- Commit `*.import` always; never commit `.godot/` (the machine-local import cache).
- `*.translation` is generated on import from the string-table source and is ignored by `platforms/kits/godot/.gitignore`; the source CSV/PO is what gets committed.

## Handling

- Never hand-edit a `.uid` file or the `uid://` strings inside `.tscn`/`.tres`.
- `.tscn` is text: read the diff in review.
- On a UID conflict take one side whole, delete `.godot/uid_cache.bin`, run `godot --headless --path . --import` and commit the regenerated files.

## Scene ownership

- Keep scenes small and single-owner: one script per scene root; children communicate by signals; no cross-scene `get_node` paths.

## Rule

- Generated files (`*.uid`, `*.import`, regenerated `.tscn`) belong in the task's `Files` cell and in the PR diff review, never silently added; `sdd-tasks` pre-cut already requires test paths in `Files`.
