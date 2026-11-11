---
type: llm
---

PASS if the answer says the function's cyclomatic complexity is above 10 (an estimate from 11 to 14, or "above the target of 10") and recommends bringing it down by splitting it (for example one function per status) or by testing each branch.
FAIL if it never mentions cyclomatic complexity or a target of 10, or if it calls the function fine to merge as it is.
