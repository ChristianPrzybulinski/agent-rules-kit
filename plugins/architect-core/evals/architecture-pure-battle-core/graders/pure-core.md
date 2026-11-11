---
type: llm
---

PASS if the answer moves the rule into a pure function or a scene-free class (for example a `RefCounted`) that receives the random roll (or a random generator) and the time (or a clock) as parameters, and leaves the node to call it and update the HUD.
FAIL if the calculation keeps calling `randf()` or the system clock itself.
