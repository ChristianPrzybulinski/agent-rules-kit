---
type: llm
---

PASS if the answer replaces the boolean flags with one mode value (an enum, a sealed type or a strategy per mode) so that adding "event" is one more case, and says the old flags go away, even if it delivers the change in steps.
FAIL if it adds a third boolean parameter such as `eventMode` or another `if` on the existing flags.
