---
type: llm
---

PASS if the answer says the null check only hides the symptom and is not a fix until the cause is named (why `get_item(slot)` returns null for that slot at login, for example the inventory not loaded yet or an out-of-range slot), and asks for a reproduction or failing test first; it may keep the guard only if the cause shows an empty slot is a legal, intended state.
FAIL if it approves adding the null check as the fix without naming or seeking the cause.
