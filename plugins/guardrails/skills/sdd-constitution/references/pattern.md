---
description: Our pattern - each spec artifact's layer in SysML, DDD, Backstage and SAFe, the SysML link names and the generated views and exports.
kind: detail
---

# Our pattern: SysML, DDD, Backstage and SAFe

Each source gives one layer, so the kit invents no vocabulary: SysML names the links, DDD fills the enabler, Backstage
names the enabler's fields and its export, SAFe names the work. Read it when writing `spec.md`, an ENB or a FEAT, or
when a link has no name.

| Our artifact | SysML | DDD | Backstage catalog | SAFe |
|---|---|---|---|---|
| Vision, pillars | — | core vs supporting domains | — | strategic themes |
| `PROC` | activity (Steps) + state machine (States) | domain process, domain events | — | part of the feature definition |
| `REQ-F` / `REQ-NF` | requirement | invariant, policy | — | story acceptance / NFR |
| `ENB` | block; ports and interfaces | bounded context, aggregates, published language | `Component` (its `system`, `domain`) | enabler (architectural runway) |
| ENB contract row | port / interface | published language | `API` (api, message, event) or `Resource` (other kinds) | — |
| `FEAT` | use case: one actor, one goal, a slice of process steps | — | none: work, not a component | feature (`kind: feature`) or enabler (`kind: enabler`) |
| task row | — | — | — | story |
| ENB `owner` | — | team per context | `Group` via `owner` | team / ART |

## Links: written once, named by SysML

| Link | From → to | Written once in | Generated in |
|---|---|---|---|
| derive | journey or process step → REQ | the step's `Rules` cell | `traceability.md` § Links (SysML) |
| refine | FEAT (use case) → REQ | FEAT `requirements` (REQ `features` mirrors it) | same |
| satisfy | ENB → REQ | ENB Aggregates (REQ-F) and Qualities (REQ-NF) `Rules` | same, and § Enablers |
| verify | test → REQ | `Proven by` of the steps that derive it | same |
| allocate | FEAT → ENB (its REQs to blocks) | FEAT `enablers`; the Plan walk table details it | same |

- One process holds N FEATs. Two FEATs with the same actor and goal, or the same process steps, are one FEAT.
- The view appears once the spec has `processes/` or `enablers/`; a spec with neither renders its matrix as before.
- Never draw SysML by hand or keep a model file: the text artifacts are the model.

## Generated outputs (`spec_trace.py`)

- `catalog SPEC --out FILE [--force]`: the ENBs as Backstage `catalog-info.yaml` (`apiVersion: backstage.io/v1alpha1`)
  at the path the caller names, never inside the kit. Component per ENB (`type: service`; `lifecycle` from `status`:
  proposed experimental, approved production, retired deprecated; `owner`, `system`, `providesApis`, `consumesApis`;
  `dependsOn` its ENBs and the Resources it requires); `domain` goes to the annotation `agent-rules-kit/domain`, as a
  Component has none. Contract kinds api → `openapi`, message and event → `asyncapi` API entities; the other kinds are
  Resources with `dependencyOf` the ENB. System, Domain and Group entities stay the portal's. Never hand-written.
- `diagram SPEC PROC-nnn`: a Mermaid flowchart of the main path and its alternatives, to stdout.
- A field an export needs that the ENB cannot hold gets an `x-` profile key (KIT-087), never a forked vocabulary.

## Sources

- [FACT] Backstage kinds, fields, lifecycles and API types: the descriptor format
  (https://backstage.io/docs/features/software-catalog/descriptor-format), read 2026-11-17.
- [HYPOTHESIS] The SysML (v1.x) relation names and the SAFe terms come from general knowledge, with no specification
  read; the owner chose them (KIT-098, E § 13.4 and § 15). A mismatch with the specification renames the link here.
