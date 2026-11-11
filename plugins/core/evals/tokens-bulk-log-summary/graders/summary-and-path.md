---
type: llm
---

PASS if the report names both failures (`test_bank_withdraw`, expected balance 50 got 0; `test_trade_cancel`, timeout after 30s) with the conclusion first, cites `ci/nightly-2026-11-10.log` for detail, and quotes no more than the failing lines; filtering the log (grep, a subagent, reading in pieces) is fine.
FAIL if the report pastes long stretches of the log (dozens of PASS lines), misses a failure, or invents a failure the log does not hold.
