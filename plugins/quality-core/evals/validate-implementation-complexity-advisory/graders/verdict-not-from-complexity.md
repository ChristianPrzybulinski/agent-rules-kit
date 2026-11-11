---
type: llm
---

PASS if the report has an `Advisory:` line with the complexity output for the changed Java method (a CRAP or CC figure, or a notice that the JaCoCo report or the complexity tool is missing) and the verdict's stated reasons do not include that complexity output.
FAIL if there is no `Advisory:` line, or if the complexity figure or its missing input is given as a reason for `PARTIAL` or `NOT READY`.
