---
name: Feature
about: One FEAT tracked by one issue; execution tasks stay in the FEAT file
title: "[FEAT-NNN] "
labels: ""
assignees: ""
---

## Outcome

<!-- The FEAT's delivery outcome. Reuse its existing issue/card; never create an issue per task or bundle. -->

## Spec

<!-- Link to docs/spec/features/FEAT-NNN.md and its task table. The FEAT owns row scope, dependencies and evidence. -->

## Repository

<!-- Affected code/spec repositories; each task row still owns its own Files. -->

## Files (owned areas)

<!-- Union of the FEAT rows' rooted paths/globs, tests included. A task PR owns only its selected rows' Files. -->

## Proof of completion

<!-- FEAT acceptance/closure proof and links to per-row proofs in the FEAT; issue closure alone is not delivery. -->

## DoD

<!-- Applicable repository gates and FEAT closure/acceptance gate. -->

## Depends on

<!-- Other FEAT issues or FEAT-nnn Tn; never a dependency on this issue for an internal task dependency. -->

## Tasks

<!-- Copy the approved FEAT task table verbatim, including ID and Files columns, preserving repository-qualified Files for the gates. The FEAT file is authoritative; refresh this mirror on resync, never maintain a separate backlog. -->

## Notes

<!-- Task PRs select ids under ## Task rows (T1, T2) and use Refs, not Closes, on this issue. Close after FEAT acceptance; reuse for later approved versions. -->
