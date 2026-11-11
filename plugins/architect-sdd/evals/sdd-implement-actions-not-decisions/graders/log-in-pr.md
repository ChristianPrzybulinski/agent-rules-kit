---
type: llm
---

PASS if the answer says no: the Decisions section holds only choices with their reason (one line each, `YYYY-MM-DD T3 (<PR>): chose X over Y because Z`), the action log and proof output go to the PR body (or History for the proof summary).
FAIL if it pastes or recommends pasting the command list into Decisions.
