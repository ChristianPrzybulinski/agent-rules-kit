---
type: llm
---

PASS if the answer says the test would still pass if the function returned 0.0, and rewrites it (or says to rewrite it) to call the rule's public entry point instead of the private `_base_chance` helper and to assert an exact expected value or outcome.
FAIL if it approves the test, or keeps both the private call and the `is_greater_equal(0.0)` assertion.
