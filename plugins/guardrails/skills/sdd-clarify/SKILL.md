---
name: sdd-clarify
description: SDD step 2 — turn a specified NEED into approved REQs by asking product. Use when a NEED is specified. Not for gap checks (skill sdd-check).
argument-hint: "NEED-nnn"
triggers:
  - user
disable-model-invocation: true
allowed-tools:
  - read
  - glob
  - grep
  - edit
  - exec
---

# SDD 2 — Clarify

The functional refinement: makes each Situation of a `specified` NEED precise as REQs, a journey step or a product decision, and ends with the NEED `refined`. No technical choice, FEAT, debt or task row. Process: `../sdd-constitution/references/sdd-process.md`. Scope rules: `references/req-scope.md`. Templates: `../../templates/spec-requirement-functional.md`, `../../templates/spec-requirement-non-functional.md`.

## 1. Map each Situation

Read the NEED, `docs/spec/spec.md` and the REQs and journeys its Triage names. For every Situation choose one, following `references/req-scope.md`:

- reuse: an existing REQ already states it; nothing changes;
- amend: an existing REQ states it differently; edit that REQ and add a History line;
- new: write a REQ-F or REQ-NF with `status: proposed` (next unused id, or the session's reserved block), its Rationale citing `NEED-nnn S<n>`;
- journey: the Situations add, change, reorder or remove a step of a flow of two or more screens or interactions, and the project keeps `docs/spec/journeys/` → `references/journeys.md`;
- decision: product must choose between two or more reasonable options → a product decision record with `status: proposed`, cited in each REQ's `source`;
- cut: out of scope, with where it goes.

Each REQ: one rule sentence and a Values table for the numbers the actor experiences; Verification with the proving test type, examples and counterexamples (from the Situations that go wrong).

## 2. Ask, one question at a time

Collect clarification markers, undefined glossary terms and vague quantities ("fast", "many", "safe"). Ask one question per call of the runtime's ask tool (`AskUserQuestion`, `ask_user_question`), else in text: one line of context with a concrete example, two to four options with consequences, and a marked recommendation. Never answer a product, cost or risk choice yourself; a technical question waits for `sdd-plan`.

Put each answer where it belongs (REQ, NEED, glossary), never in an answers section, and record `YYYY-MM-DD clarify: <question> → <answer>` in the NEED's History. A vague quantity becomes a number or a `[HYPOTHESIS]` with its measurement method. An answer that reveals a new Situation returns the NEED to `sdd-specify` part 2.

## 3. Record and check

- Fill the NEED's Refinement table (one row per Situation: what it became and why) and its `requirements`, `journeys` and `decisions` fields.
- Run the project spec validator (and `spec_trace.py check` when journeys exist), then `sdd-check NEED-nnn` (functional mode). A critical or high finding goes back to the step that owns it.

## 4. Close

With no open question, a clean functional check and product's approval of the REQs, journeys and decisions: set the REQs `approved`, the journeys and product decisions `approved`, the NEED `refined`, and add `YYYY-MM-DD clarify: refined` to its History.

## Rules

- One behavior or quality per REQ; amend an existing REQ instead of writing a second one for the same behavior.
- No algorithm, message, table or framework in a REQ; no FEAT, debt or task row in this step.

Done when: every Situation maps to a REQ, a journey step, a decision or a cut; no clarification marker remains; the functional check is unblocked; and the NEED validates as `refined` with its links filled.
