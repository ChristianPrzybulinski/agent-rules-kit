---
name: investigate
description: Root-cause investigation with reproduction. Use when a bug, slow behavior or incident has no named cause. Not for implementing fixes (skill sdd-implement).
argument-hint: "[symptom description | log/issue link]"
triggers:
  - user
  - model
subagent: true
context: fork
background: false
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Investigate

## 1. Pin down the symptom

Record observed and expected behavior, environment, commit/version, platform, frequency and the source of the expectation. Treat third-party reports as hypotheses until reproduced, and rule out an expected state (a deploy, restart, migration or rollout in progress) before calling it a fault.

## 2. Reproduce before proposing a fix

- Prefer an automated failing test, then a script, then numbered manual steps.
- A bug fix starts only after a test fails for the right reason; the failing test defines the defect boundary.
- If reproduction fails, record attempts and missing data/access instead of editing by intuition.
- A CI-only failure: save the failed job log to a file (`gh run view <run> --log-failed > <scratch>/ci.log`), quote its first error byte-for-byte with the path, and reproduce under CI conditions; a flaky test is rerun N times there and reported as passes/N.
- For slowness, capture a number, tool and command before calling it a performance problem.

## 3. Prove the executed path

- Use logs, a debugger, trace or temporary instrumentation to show which path ran.
- List competing hypotheses, each with the observation that would refute it; test the cheapest refutation first, against a passing case that differs in one variable.
- Bisect only when a verified good commit exists.
- Name a cause only when the evidence shows that code executing in the reported scenario; otherwise state the next discriminating observation.

## 4. Record impact and regression proof

- For money, inventory or data incidents, verify affected counts by query rather than estimate.
- Define the regression test that must remain after the fix; do not implement the fix in this skill.
- Once the cause is named, search for the same defect elsewhere (`git grep` the pattern, the other callers of the boundary) and list each sibling as fixed in this change or as a follow-up issue.
- A guard that only hides the symptom (null check, catch-all, retry, default value) is not a fix unless the cause is named and the guard is the intended behavior; fix at the boundary that produced the bad value, not where it surfaced.
- Remove temporary instrumentation unless it becomes deliberate structured logging; when no log or check showed the cause, propose the one always-on log line, metric or assertion that would have.

## 5. Report

Report symptom, reproduction, cause/evidence, impact, proposed fix and required test. A race/cache explanation needs a concurrent test or trace.

Done when: the symptom reproduces deterministically and has a source-backed cause, or the report names exactly what evidence is still missing.
