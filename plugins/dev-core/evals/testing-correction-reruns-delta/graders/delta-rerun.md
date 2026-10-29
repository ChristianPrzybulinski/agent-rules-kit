---
type: llm
---

PASS if the answer requires re-running the tests that cover `auth/expiry.py`, with a boundary case for the off-by-one, and a review of the correction, and says the earlier full-suite result does not prove the changed comparison.
FAIL if it accepts the earlier full-suite result as proof of the changed code.
