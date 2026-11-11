---
type: llm
---

PASS if the answer writes one line in the FEAT's `## Decisions` section in the form `YYYY-MM-DD T2 (#88): chose a sorted array over a Dictionary because ...` (the date may be a placeholder).
FAIL if the choice goes only into the PR body, a commit message or History, or if the Decisions entry lists the commands that were run instead of the choice and its reason.
