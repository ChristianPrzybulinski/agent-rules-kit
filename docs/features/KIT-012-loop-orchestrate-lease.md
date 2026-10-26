---
id: KIT-012
title: "loop-orchestrate takes the coordinator lease before waiting"
status: done
confirmed: "2026-10-26 (owner, Stratics FEAT-101 activation coordination chat)"
issue: "#92"
pr: "#93"
---

# KIT-012 — loop-orchestrate takes the coordinator lease before waiting

## Problem and evidence

[FACT] stratics-docs#2697 (merged 2026-10-26 as `023f17c99`) turned on `provider_neutral_workflow.enabled` in
`platform/review-loop/config.json`. With it on, `loop.py wait --role claude` exits with `no-lease` unless the batch
holds a coordinator lease taken by `loop.py coordinate resume --provider claude --session <id>` and the waiter is
called with `--as-provider claude --session <id>`. The test `ShippedActivation` in
`platform/review-loop/tests/test_agent_routing.py` asserts the refusal. Step 4 of
`plugins/process-loop/skills/loop-orchestrate/SKILL.md` armed the bare `wait --role claude`, so an orchestrator
following the skill stops at its first wait.

## Change

- `plugins/process-loop/skills/loop-orchestrate/SKILL.md` § 4 gains: "When the loop guards coordination with a lease
  (its `wait` refuses with `no-lease`), take it first with `<loop> coordinate resume --provider claude --session <id>`
  and arm `<loop> wait --role claude --as-provider claude --session <id>`, where `<id>` is this session's ID as the
  CLI reports it; never invent one."

## Proof

`bash platforms/tools/check.sh`, `bash platforms/tools/smoke.sh`,
`python3 platforms/ci/validations/check_kit.py --links`.

## History

- 2026-10-26: confirmed (owner, chat); implemented in #93.
