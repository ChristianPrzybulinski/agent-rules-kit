---
id: ENB-000
title: "[Bounded context or technical capability: Battle]"
status: proposed
owner: "[the team that owns the context]"
system: "[the system it belongs to, or delete the line]"
domain: "[the domain it belongs to, or delete the line]"
providesApis: []
consumesApis: []
dependsOn: []
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
---

# ENB-000 — [Title]

<!-- An enabler: the living description of one DDD bounded context or technical capability and the contracts it
     provides and requires (KIT-095). A FEAT is the frozen delivery: its `enablers` names the ENBs it creates or
     changes, and its Plan § Contract cites the catalog rows below as `ENB-000:<contract>` instead of restating them.
     Spec-anchored: the PR that changes a contract updates its row here (skill sdd-implement, living-docs.md).
     Frontmatter: Backstage's field names. `providesApis` lists every Contract id of Provided contracts and
     `consumesApis` every Contract id of Required contracts, the same ids as the tables (spec_trace.py checks both);
     `dependsOn` names the ENBs this one needs at run time.
     Register (skills/sdd-constitution/references/sdd-process.md, Register): technical documentation; it cites a REQ
     and never restates its rule. -->

## Context

- Bounded context: [one line: what the context decides and what it leaves to others]
- Ubiquitous language: [the glossary terms it owns, as in spec.md Glossary]
- Patterns: [the patterns in use, from skill sdd-plan's pattern catalog]

## Aggregates

| Aggregate | Invariant | Rules |
|---|---|---|
| [aggregate] | [what it always keeps true] | REQ-F-nnn |

## Events

| Event | Direction | Contract |
|---|---|---|
| [domain event] | publishes / consumes | [contract id of Provided (publishes) or Required (consumes) contracts, or —] |

## Provided contracts

| Contract | Kind | Accessed at | Schema or file | Version | Consumers |
|---|---|---|---|---|---|
| [contract-id] | api / message / event / job / file / table / content / config | [endpoint, channel, schedule or path] | `[rooted path or glob]` | [version] | [ENB-nnn, a client or public] |

## Required contracts

| Contract | Kind | From | Used for |
|---|---|---|---|
| [contract-id] | [kind] | ENB-nnn | [one line] |

## Qualities

| Quality | Target | Rules |
|---|---|---|
| [p95 latency, frame budget, availability] | [target and unit] | REQ-NF-nnn |

## Code

- `[rooted/path/**]`

## Decisions

Generated: `traceability.md` § Enablers lists the decisions and debts whose `enablers` names this ENB.

## History

Generated: `traceability.md` § Enablers lists the FEATs whose `enablers` names this ENB, with their status.

<!-- Notes the checkers enforce (check_spec.py on the frontmatter, spec_trace.py on the tables):

  - A Contract id is lowercase letters and digits joined by `.`, `_` or `-`, unique across every ENB; a Required
    contract's `From` is the ENB that provides it.
  - Kind is one of api (endpoint), message (wire), event, job (schedule), file (path and layout), table
    (migration), content (pack key) or config.
  - `Schema or file` holds backticked paths or globs rooted at the repository: `spec_trace.py enablers` (C19) fails a
    protocol schema (sdd.row_checks.protocol.schemas) or a `--catalog` file no row covers.
  - Consumers names ENB ids, a client, or `public`; a contract with none is a C19 finding.
  - Aggregates `Rules` cites REQ-F ids and Qualities `Rules` REQ-NF ids, never their text: these rows are how an ENB
    satisfies a REQ, and a REQ (not `retired`) or process step no ENB satisfies is a C18 finding.
  - Decisions and History are generated, never written here: a FEAT, decision or debt names the ENB in its own
    `enablers` field.
-->
