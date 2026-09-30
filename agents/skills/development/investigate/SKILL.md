---
name: investigate
version: "1.0"
description: Investigates a bug, regression, performance problem or incident to a named root cause, with reproduction before any fix. Use when something "doesn't work", is slow, or failed in production/CI. Do not use to implement the fix (that returns to the normal flow with a failing test first).
argument-hint: "[symptom description | log/issue link]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Investigate

A symptom is not a cause. This skill ends when there is a deterministic reproduction and a named cause in the code — or when it is clear what is missing to get there.

## 1. Pin down the symptom

- What was observed, where (environment, version/commit, platform), when, how often.
- What was expected, and why (spec, test, doc, or just the user's expectation — say which).
- A third-party report (issue, chat, memory) is `[HYPOTHESIS]` until reproduced.

## 2. Reproduce

- The shortest path that triggers the symptom: automated test > script > numbered manual steps.
- Couldn't reproduce → do not "fix by intuition". Record the attempts and what is missing (data, environment, access).
- Performance: measure first (number + tool + command), not "seems slow".

## 3. Narrow down

- Bisect when a known-good commit exists (`git bisect`).
- Read the code path actually executed (logs, breakpoints, temporary `print`), not the one that "should" run.
- List competing hypotheses and look first for the evidence that **refutes** each.
- A hypothesis becomes the cause only when it explains the whole symptom and the evidence shows that code executing in the scenario.

## 4. Report

Template: `agents/templates/doc-bug-report.md` (symptom, reproduction, cause, evidence, impact, proposed fix, the test that must now exist). Destination: project issue or `docs/incidents/` per `AGENTS.md`.

Incident with data/money/inventory affected → impact section with a count verified by query, not an estimate.

## Rules

- Fix only after a test that fails for the right reason (`agents/rules/development/testing.md`).
- Remove temporary instrumentation before committing; if it stays, it is deliberate structured logging.
- A "race condition" or "cache" cause requires a demonstration (concurrent test or trace), not plausibility.
- Do not close with "not reproduced" without listing what was tried.
