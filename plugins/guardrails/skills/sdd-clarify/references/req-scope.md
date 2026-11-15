---
description: What a REQ is, REQ-F versus REQ-NF, when a NEED becomes one REQ or several, and what goes elsewhere. Load when writing or amending a REQ.
kind: detail
---

# REQ scope

A REQ is one behavior (REQ-F) or one quality (REQ-NF) that product commits to and a test proves. It states the current truth: amending it is an edit plus a History line, never a second REQ for the same behavior.

## 1. In a REQ, or elsewhere

| In the REQ | Elsewhere |
|---|---|
| actor, condition, visible result | how the code does it (algorithm, draw order, data structure) → technical step (Plan, tech decision) |
| a number or formula the actor experiences (odds, limit, reward, damage) | why one option over others → product decision record; the REQ cites it in Rationale |
| examples and counterexamples | the order of steps in a flow → journey |
| | position and look on screen → approved mock, screen spec; the REQ says what is shown, not where |
| | a tuning value that changes without changing the rule → content; the REQ names the rule and the value's source |
| | a contract, message or endpoint → technical step |

## 2. REQ-F or REQ-NF

| | REQ-F | REQ-NF |
|---|---|---|
| answers | what the system does for an actor in a situation | how well, measured over many runs or across many behaviors |
| form | one rule sentence + optional Values table | one sentence + metric, target (or hypothesis) and measurement |
| proof | a scenario: example and counterexample | a measurement: benchmark, load, timing, audit |

- A number that is part of the rule the actor sees → REQ-F ("a party holds at most 6").
- A measured target (p95, %, MB, frames, uptime) → REQ-NF.
- Authorization per action and entity ("no one trades another player's item") → REQ-F; a property across behaviors ("no secret reaches a log", "every endpoint is rate-limited") → REQ-NF.
- "Fast", "smooth", "holds N users", "always up", "secure" in a NEED ask for a REQ-NF, or a hypothesis with its measurement.

## 3. One REQ or several

Split when any holds:
1. another actor (user, admin, scheduled job);
2. another trigger with another result;
3. it can fail alone: a test could break one and pass the other;
4. it can change alone: a later NEED would change one without the other;
5. a behavior mixed with a quality (F with NF);
6. a rule and its display: the rule and what a screen shows are proved differently.

Keep one REQ when:
- the same rule applies in several places: one REQ lists the places;
- it is the sad path of the same behavior: a counterexample of that REQ, unless it carries its own product rule (penalty, refund, specific message);
- it is a sequence of steps: the journey orders them and cites each REQ.

Every Situation of the NEED becomes a REQ, a journey step or a cut (the NEED's Refinement table), and every REQ cites its Situation in Rationale or `source`.

## 4. When the NEED touches other artifacts

| Signal while refining | Goes to |
|---|---|
| a product choice between two or more reasonable options, or a policy several REQs follow | product decision record, `status: proposed` |
| a new or changed flow of two or more screens or interactions | journey (`journeys.md`), when the project keeps journeys |
| a changed look | approved mock, recorded as the NEED's evidence |
| a behavior an existing REQ already states | amend that REQ |
| a technical choice, a delivery shortcut or a debt | never here: the technical step (`sdd-plan`) and delivery |
