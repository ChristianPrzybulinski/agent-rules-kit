---
type: llm
---

PASS if the message has a Conventional Commits title (for example `fix(shop): reject non-positive purchase quantity`) and a body that states why (negative quantity accepted, #57), what changed (the rejection and the boundary tests) and the proof (the command and its result).
FAIL if the body omits the proof or the reason, or the title is not Conventional Commits.
