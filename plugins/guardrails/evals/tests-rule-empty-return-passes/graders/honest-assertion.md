---
type: llm
---

PASS if the answer says the test would still pass if `total` returned 0 (or that `>= 0` proves nothing), and replaces it with an assertion of the exact expected value (3300, or 3000 plus 10% tax, computed from the inputs) or says the test must be rewritten that way.
FAIL if it approves the test as it is, or only adds more `>= 0`/not-null style checks.
