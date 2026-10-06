---
name: sdd-journey
description: "Journey layer — J-NN steps cite REQ ids, tasks and tests. Use when writing a user-visible flow. Not for FEATs (skill sdd-specify)."
argument-hint: "J-NN | <stage or flow>"
triggers:
  - user
disable-model-invocation: true
allowed-tools:
  - read
  - edit
  - exec
---

# SDD — Journey

Process: `../sdd-constitution/references/sdd-process.md`. A journey is one user-visible flow; it cites rule ids, task rows and tests — never rule values. Template: `../../templates/spec-journey.md`.

## 1. Write the journey

- Create `docs/spec/journeys/J-NN.md` from the template: `status: proposed`, `owner`, `created`, `updated`.
- Step tables (first header cell `Step`): `S<n>` main path in order, `A<n>` alternative with `At` naming its main step, `P<n>` prerequisite (contracts, assets, tooling no user sees).
- `Rules` holds REQ ids only or `—`; `Implemented by` holds `FEAT-nnn Tn` rows as they are on main; `Proven by` holds test tasks, backticked paths rooted at a clone name, and an optional trailing `manual: <check>`.

## 2. Promote the rules

- Each FEAT-local rule a journey cites becomes a REQ-F in the same PR: one rule per REQ — Statement, Rationale quoting the FEAT line, Verification with a proving test and a counterexample.
- The REQ is then canonical: the FEAT decision lines stay as dated history and the task row cites the REQ id next to its value. No backfill — a rule no journey uses stays FEAT-local.

## 3. Link once, generate

- Journey → rule, task and test are written only in the journey; FEAT `requirements:` ↔ REQ `features:` stay symmetric on both sides. No FEAT, REQ or task lists journeys.
- Regenerate the matrix with the project's copy of the validator (`spec_trace.py generate`, then `check` must pass), e.g. `.github/spec-lint/spec_trace.py docs/spec` — synced by `platforms/tools/sync-project.sh`.
- Product signs the journey: `status: approved`; a retired flow is `retired`, never deleted.

## Rules

- Never write a rule value in a `Rules` cell, never list journeys inside FEATs or REQs, never edit `traceability.md` by hand.

Done when: `spec_trace.py check` is green, every cited REQ exists and is symmetric, and the matrix is regenerated.
