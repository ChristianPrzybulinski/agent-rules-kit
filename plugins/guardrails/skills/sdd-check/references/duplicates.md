---
description: Duplicate rows C20-C24 for sdd-check § 1 g - what spec_trace.py similar reports, which lines are findings and how to judge a candidate.
kind: detail
---

# Duplicates (C20–C24)

One rule, one process, one contract and one use case each live in one place (KIT-097). The NEED-level search stays in `sdd-specify` ("a NEED with the same request"); these rows extend it to REQs, processes, ENBs and FEATs. The tool is `TRACE similar <spec_root>`: read-only, the whole spec at once, one line per pair or collision, then a summary line `similar: N findings (C21, C24), M candidates (C20, C22, C23); …`.

## What the tool compares

Words compare after one deterministic normalization: casefold, claim tags (`[FACT]`, `[HYPOTHESIS]`, `[DECISION]`, `[PROPOSAL]`) and punctuation removed, stop words (articles, prepositions, auxiliaries such as `must`) dropped, word order ignored. `not` and `no` count. Retired REQs and processes and cancelled FEATs take no part.

| Row | Line | Compared | Kind |
|---|---|---|---|
| C20 | `C20 candidate: REQ-a ~ REQ-b: <reason>` | the statement's actor, trigger and result when it has the template's form ("The system must <result>, when <trigger>, for <actor>."), else the statement's words, else the title's words; the first reason that holds | judgment |
| C21 | `C21 high: contract <id> is provided by ENB-a and ENB-b` | each ENB's Provided contracts (`check_spec.py` fails it too, rule `enabler-contract`) | mechanical |
| C22 | `C22 candidate: PROC-a ~ PROC-b: same trigger and actor (<actor>)` | the Trigger section's words, and one Actors line in common | judgment |
| C23 | `C23 candidate: FEAT-a ~ FEAT-b: same actor and goal` or `same steps PROC-nnn Sn, …` | the Scope line `- Use case: <actor> <goal>`, and the process steps both FEATs' `processes` declare | judgment |
| C24 | `C24 high: REQ-x is in the open blocks FEAT-a 0.3.0 and FEAT-b` | the open block's Scope REQs of a versioned FEAT (its last block, not validated, delivered or cancelled), or the `requirements` of an open FEAT without `## Versions` | mechanical |

The tool exits 1 on a C21 or C24 line and 0 with candidates only, so its exit code says whether a mechanical finding exists, not whether a candidate is a duplicate.

## Judge a candidate

Read both artifacts, then decide:

- C20, a duplicate: one actor, one trigger and one observable result in other words, or one rule split across two REQs. Keep the older REQ; the newer one is retired with a History line, or amended into a different rule. Two rules that share a shape (a username and a character name with the same length limits) are not duplicates: note them.
- C22, a duplicate: both processes run the same flow from the same start. Keep one; the other's steps move into it, or it cites the first (`PROC-nnn S<a>–S<b>`). Two processes the same event starts that do different work (a release step that tags and one that deploys) are not: note them.
- C23, a duplicate: the same use case written twice, or two FEATs delivering the same process steps. The newer work becomes the next version block of the existing FEAT (one FEAT per use case, KIT-096). Two use cases that share a step on purpose (a login both start from) stay; note the step.

A judged duplicate is one `high` finding on the newer artifact; a candidate judged legitimate is one line in the report's notes, with the reason.

## Fix a finding

- C21: one ENB provides the contract; the other lists it in Required contracts with `From` naming the provider.
- C24: the REQ stays in one open block; the other FEAT drops it from its Scope or `requirements`, or waits for the first block's delivery (`Depends on`). A legacy spec with many open FEATs may list old collisions in `docs/spec/baseline.json` under `C24` per FEAT id, as the skill's `all` scope reads it; the file only shrinks.

Routing: skill § 4.
