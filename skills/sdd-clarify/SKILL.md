---
name: sdd-clarify
version: "1.1"
description: SDD step 2 — resolve ambiguous FEAT criteria. Use when a FEAT has open questions or vague terms. Not for quality auditing (skill sdd-audit).
argument-hint: "FEAT-nnn"
triggers:
  - user
allowed-tools:
  - read
  - edit
  - ask_user_question
---

# SDD 2 — Clarify

Process: `../sdd-constitution/references/sdd-process.md`.

## 1. Find product ambiguity

Read the FEAT and linked requirements. Collect clarification markers, criteria without a sad path, undefined glossary terms and vague quantities such as “fast”, “many” or “safe”.

## 2. Ask one focused round

Prioritize scope/risk questions. Ask at most five per round in one `ask_user_question` call; each has one-line context, two to four options, consequences and a marked recommendation.

Do not answer a product, cost or risk choice yourself. Route a technical decision to `sdd-plan` and a DEC.

## 3. Incorporate answers

Edit the criterion, scope, requirement or glossary where the answer belongs; do not append an answers section. Record `YYYY-MM-DD clarify: <question> → <answer>` in History.

## 4. Close ambiguity

Repeat only if markers remain. Set `status: clarified` when every vague quantity is numeric or a hypothesis with a measurement method.

Done when: no clarification markers remain, criteria include relevant sad paths, new terms are in the glossary and product choices came from the user.
