---
name: sdd-clarify
version: "1.0"
description: SDD step 2 — resolves a FEAT's [NEEDS CLARIFICATION] markers with objective questions (2-4 options each) to the product, incorporates the answers into the spec and moves status to clarified. Use when the FEAT has open questions or ambiguous criteria. Do not use to write the FEAT from scratch (skill sdd-specify) or to audit its quality (skill sdd-audit).
argument-hint: "FEAT-nnn"
triggers:
  - user
allowed-tools:
  - read
  - edit
  - ask_user_question
---

# SDD 2 — Clarify

## Steps

1. Read the FEAT and its linked REQs. Collect: `[NEEDS CLARIFICATION]` markers, criteria without a sad path, terms missing from the glossary, vague quantifiers ("fast", "many", "safe").
2. Prioritize: questions that change scope or architecture first. Maximum **5 per round**; if any remain, a second round.
3. Each question: context in 1 line + 2-4 options with each one's consequence + a marked recommendation. A single `ask_user_question` call per round.
4. Incorporate the answer **in the right place** (criterion, scope, requirement), not in an "answers" section. Record in *History*: `YYYY-MM-DD clarify: <question> → <answer>`.
5. An answer that is a technical decision → do not incorporate here; note it for `sdd-plan`/`DEC`.
6. Zero markers remaining → `status: clarified`.

## Completion criteria

- No `[NEEDS CLARIFICATION]`; no vague quantifier without a number or a `[HYPOTHESIS]` with a measurement method.
- `spec.md` glossary updated with new terms.

## Do not

- Answer a product question yourself "to avoid bothering". A reversible technical decision → decide and record `[PROPOSAL]`; a product/cost/risk decision → ask.
