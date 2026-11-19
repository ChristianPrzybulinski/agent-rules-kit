---
type: llm
---

PASS if the answer routes the finding as a fix task row on FEAT-001 (the FEAT whose row holds `src/login.py`) that cites REQ-F-001 and the evidence, with no NEED file.
FAIL if it records the finding as a NEED (a new `NEED-nnn`, a file in `docs/spec/needs/`, or an instruction to run `sdd-intake` §§ 1-3) or leaves the finding unrouted.
