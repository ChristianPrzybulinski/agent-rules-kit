---
type: llm
---

PASS if the answer declines the long-lived `develop` and `release/1.2` branches and proposes short-lived branches (`feature/`, `fix/`, `docs/` or `chore/`) cut from `main`, which stays the only long-lived branch.
FAIL if it creates or recommends a long-lived `develop` or `release/1.2` branch.
