---
type: llm
---

PASS if the answer models the states as types so an illegal combination cannot be constructed: for example a sealed interface with one record per state (each holding only its own fields, validated in its constructor), or an enum for the status plus per-state types.
FAIL if it keeps the string status and nullable fields and only adds validation methods or checks.
