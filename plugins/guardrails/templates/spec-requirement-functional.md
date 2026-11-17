---
id: REQ-F-000
title: "[The system must ... — 1 testable sentence]"
type: functional
status: proposed
priority: must
features: []
source: "[NEED-nnn S<n> | legacy:<path> | <decision id>]"
created: "YYYY-MM-DD"
---
<!-- Written by sdd-clarify from a NEED Situation; scope and split rules: skills/sdd-clarify/references/req-scope.md.
     status: proposed → approved (product, when its NEED is refined) → retired (never deleted). Absent means approved.
     features is filled by sdd-plan; until then the NEED that lists this REQ is its link.
     Register (skills/sdd-constitution/references/sdd-process.md, Register): PO, functional: the rule and the values
     the actor experiences, never how the code does it. -->

# REQ-F-000 — [Title]

## Statement

The system must [observable behavior], when [condition], for [actor].

<!-- One rule sentence. Numbers or formulas the actor experiences go in Values. How the code does it (algorithm, draw
     order, data structure, message) belongs to the technical step, never here. Tunable: `fixed` when the rule itself
     sets the value, else its range and unit and its exposure (where it is tuned: content, config or a debug control),
     so a retune within the range is no REQ or decision change; the code reads it from there, never a literal. -->

| Value | Meaning | Tunable |
|---|---|---|
| [number or formula] | [what the actor experiences] | [`fixed` \| <min>–<max> <unit>, <exposure>] |

## Rationale

[Why: the NEED Situation it comes from (NEED-nnn S<n>) and the decision it follows, if any. From legacy: cite the file
and mark `[FACT]` or `[HYPOTHESIS]`.]

## Verification

- Proving test: [type: unit / integration / contract / e2e + description in 1 line]
- Examples: input `[...]` → output `[...]`
- Counterexamples: [what would violate this requirement — taken from the Situations that go wrong]
- Mock (a screen only): [path of the mock product approved, the visual reference the review compares against]

## Features that implement it

- `FEAT-000` <!-- sdd-plan -->

## History

- YYYY-MM-DD NEED-nnn: created — [why, one line].
