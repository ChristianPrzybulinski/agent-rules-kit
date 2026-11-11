---
type: llm
---

PASS if the design makes the step idempotent and crash-safe: the file is deleted (or archived) only after the write is confirmed, and the write is keyed (upsert or a unique key) so a rerun after a half-way crash gives the same rows.
FAIL if it keeps deleting before the write, or if rerunning would insert duplicate players.
