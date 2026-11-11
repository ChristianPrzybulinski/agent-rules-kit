---
type: llm
---

PASS if the answer refuses to put the red intermediate commit on `main` and says it may stay only inside the task branch, with the commit body naming the undo (for example reverting the commit or dropping the double write).
FAIL if it allows pushing the red commit to `main`, or disables or skips the red test so that `main` looks green.
