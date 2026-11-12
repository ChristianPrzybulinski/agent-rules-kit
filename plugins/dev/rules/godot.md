---
description: Always/never constraints for GDScript, scenes and project.godot; procedures stay in skill godot-standards.
trigger: glob
globs:
  - "**/*.gd"
  - "**/*.tscn"
  - "**/project.godot"
paths:
  - "**/*.gd"
  - "**/*.tscn"
  - "**/project.godot"
---

Always/never for `*.gd`, `*.tscn` and `project.godot`. Procedures: skill `godot-standards`.

- Always: Godot 4 syntax only: `@onready`, `@export`, `await`, `instantiate()`, `signal_name.connect(callable)`. Never `onready var`, `export`, `yield`, `instance()`, `connect("name", ...)`.
- Always: typed GDScript: `var speed: float = 120.0`, `func hit(dmg: int) -> void`; an untyped variable, parameter or return is a defect.
- Never: `@warning_ignore` to hide an untyped or unused warning (type it or delete the code); any other sits on the narrowest line with a comment naming why.
- Never: `get_parent()` or an ancestor lookup to apply a game rule; use signals or the project's `EventBus` autoload.
- Never: an authoritative game rule on the client; the client sends intent, predicts only what the repo `AGENTS.md` allows and reconciles on the server's answer.
- Always: new or changed logic ships with a gdUnit4 test under `tests/` (GUT only when the repo `AGENTS.md` says so).
- Always: `.uid`, `*.import` and `.translation` files travel with their source in the same commit and in the task's `Files` cell.
- Never: edit `.godot/`, a `.uid` file or a generated `*.import` by hand.
- Always: boot proof before "done": `godot --headless --path . --import` then `! godot --headless --path . --quit 2>&1 | grep -Eq 'SCRIPT ERROR|Parser Error'`; paste the literal output.
