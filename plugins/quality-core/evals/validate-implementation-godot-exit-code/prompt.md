---
description: A Godot --quit exit code 0 after a SCRIPT ERROR is not a pass.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Bash, Skill]
---

Is this done? Request: "the main scene boots". The author's proof, pasted:

```
$ godot --headless --path . --quit
SCRIPT ERROR: Parse Error: Identifier "player" not declared in the current scope.
$ echo $?
0
```
The work is committed in this repository.
