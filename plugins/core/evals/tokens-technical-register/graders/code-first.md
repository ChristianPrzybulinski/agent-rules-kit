---
type: llm
---

PASS if the answer leads with the corrected line (`print("building")`) or a diff, keeps the error text exact when it quotes it, and has at most about three lines of prose.
FAIL if it opens with a long explanation of Python 2 versus 3 before the fix, or paraphrases the error incorrectly.
