---
name: validate-implementation
version: "1.0"
description: Validates whether an implementation is truly done — confronts what was delivered with the spec/feature (FEAT-xxx) or the request, runs the project gates, checks docs and issues a READY / PARTIAL / NOT READY verdict with evidence. Use before opening a PR, when closing a task, or when someone claims "it's done". Do not use to fix what fails (back to sdd-implement) or to audit the spec itself (skill sdd-audit).
argument-hint: "[FEAT-xxx | spec path | description of what should be done]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Validate Implementation

"Done" requires observation. This skill produces the observation. It fixes nothing: it only measures and reports. Fixes go back to the normal flow (or `sdd/implement`).

## 1. Pin down the target

- Argument is `FEAT-xxx` → read `docs/spec/features/FEAT-xxx.md`; acceptance criteria and linked requirements (`REQ-*`) are the target.
- Argument is a path/description → extract verifiable criteria; if there are none, stop and ask for 1-3 criteria.
- List each criterion as a row of the final table **before** verifying.

## 2. Verify what exists (not what was said)

- `git diff <base>...HEAD --stat` and `git log`: what actually changed. Files cited in the report but absent from the diff → flag.
- For each criterion: locate the code that implements it (`grep`), the test that proves it, and the doc that records it.
- A criterion without a test → does not count as met.

## 3. Run the project gates

Read the repo's `AGENTS.md`/README for the canonical commands. Kit default:

| Stack | Command |
|---|---|
| Java/Maven | `./mvnw -q spotless:check verify` (includes JaCoCo, PITest, Dependency-Check per the POM) |
| Godot | `godot --path . --headless --quit` + the project's test runner |
| Docs/spec | the kit's `platforms/tools/check.sh` or the project's spec lint |

Literal output of what failed goes in the report. Do not summarize as "some tests failed".

## 4. Closing checklist (from `../update-docs/references/living-docs.md`)

CHANGELOG `Unreleased` · README if a command changed · Javadoc/docstring on new public API · `FEAT` status updated · `DEC`/`DEBT` created if a decision/debt happened · feature flag recorded if incomplete.

## 5. Verdict

```
Target: FEAT-xxx — <title>
Verdict: READY | PARTIAL | NOT READY
Gates: <command> → OK | FAILED (<literal excerpt>)
| Criterion | Code | Test | Doc | Status |
|---|---|---|---|---|
| ... | path:line | path | path | ✓ / ✗ / partial |
Unverified: <what could not be measured and why>
Next step: <the smallest action that changes the verdict>
```

## Rules

- READY only with all criteria ✓ and gates OK. One ✗ → PARTIAL. A failing gate → NOT READY.
- Do not accept "tested manually" without a reproducible step.
- If the spec is ambiguous enough to prevent judging a criterion → report it as a spec gap (not a code gap) and suggest `sdd/clarify`.
