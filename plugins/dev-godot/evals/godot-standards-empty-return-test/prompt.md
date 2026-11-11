---
description: A gdUnit4 test that passes on empty returns is rewritten through the public entry.
tags: [ready]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Is this gdUnit4 test for our capture rule good enough? `CaptureRule` is a `RefCounted` with `class_name`.

```gdscript
extends GdUnitTestSuite

func test_capture() -> void:
    var rule := CaptureRule.new()
    var chance: float = rule._base_chance(30, 100)
    assert_float(chance).is_greater_equal(0.0)
```
