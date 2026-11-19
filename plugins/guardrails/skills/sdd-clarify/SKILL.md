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

The functional refinement: makes each Situation of a `specified` NEED precise as REQs, a journey or process step or a product decision, and ends with the NEED `refined`. No technical choice, FEAT, debt or task row. Process: `../sdd-constitution/references/sdd-process.md`. Scope rules: `references/req-scope.md`. Templates: `../../templates/spec-requirement-functional.md`, `../../templates/spec-requirement-non-functional.md`, `../../templates/spec-process.md`.

Resolve the project profile first (`../session/references/project-profile.md`): `spec_root` (every `docs/spec` here) and `sdd`. With `sdd.flow: feat-only` (the `tooling` preset, KIT-100) this step does not run: there is no REQ, so say so and hand the request to `sdd-plan`, whose FEAT holds the rules in its acceptance criteria (`../../templates/spec-feature-lite.md`). With `sdd.needs: false` (`../sdd-constitution/references/sdd-parameters.md`) there is no NEED: map the Situations `sdd-specify` settled, write REQs with `source: request YYYY-MM-DD S<n>`, and put each answer in its REQ or in the FEAT's Problem section instead of a NEED's History; skip the Refinement table and `sdd-check NEED-nnn`, and hand the approved REQs to `sdd-plan`, since `check_spec.py` requires each REQ to have its FEAT: the REQs land in the change that creates it, and `sdd-plan`'s full-scope check covers them.

## 1. Map each Situation

Read the NEED, `docs/spec/spec.md` and the REQs, journeys and processes its Triage names. Work each Situation as an example map: the rules it implies become REQs, its examples and counterexamples become their Verification, and what is still unknown becomes a question for §2. A size L NEED or a new area may start with a short event-storming pass (domain events, the commands that cause them, the rules between). For every Situation choose one, following `references/req-scope.md`:

- reuse: an existing REQ already states it; nothing changes;
- amend: an existing REQ states it differently; edit that REQ and add a History line;
- new: write a REQ-F or REQ-NF with `status: proposed` and `source: NEED-nnn S<n>` (next unused id, or the session's reserved block);
- journey: the Situations add, change, reorder or remove a step of a flow of two or more screens or interactions, and the project keeps journeys (`sdd.journeys`; absent = on when `docs/spec/journeys/` exists) → `references/journeys.md` (journeys and processes: a step reused from another flow cites its process, `PROC-nnn` or `PROC-nnn S<a>–S<b>`, and the NEED lists it in `processes`); a new step holds `—` in `Implemented by` and `Proven by` until `sdd-tasks` fills them, and the NEED lists the journey in `journeys`;
- process: the Situations add or change a flow two flows share, one journey would copy from another, no user sees, or one mechanic with states → `references/processes.md` (states with entry, duration and unit, experience and exit; a branch row per decision outcome; the feedback each actor action gets); its new steps hold `—` until `sdd-tasks` fills them, and the NEED lists the process in `processes`;
- decision: product must choose between two or more reasonable options → a product decision record with `status: proposed`, cited in each REQ's Rationale;
- cut: out of scope, with where it goes.

Each REQ: one rule sentence and a Values table for the numbers the actor experiences, each with its `Tunable` cell (`fixed`, or range, unit and exposure: `references/req-scope.md` § 1); Verification with the proving test type, examples and counterexamples (from the Situations that go wrong); a REQ about a screen also cites the mock product approved. A rule that must always hold (an invariant, such as a maximum count) is a REQ of its own, which `sdd-plan` maps to what protects it. Every domain term a REQ uses is in the `spec.md` glossary; add a missing one in the same change.

## 2. Ask, one question at a time

Collect clarification markers, undefined glossary terms and vague quantities ("fast", "many", "safe") as a tree: each question hangs off the answers it needs. The frontier is every open question whose prerequisites are settled; ask only from it, the question most others depend on first, and recompute it after each answer, never asking one whose answer hinges on a question still open. A fact you can look up (code, files, the spec) is yours to find, never a question. Ask one question per call of the runtime's ask tool (`AskUserQuestion`, `ask_user_question`), else in text: one line of context with a concrete example, two to four options with consequences, and a marked recommendation. Ask it before a long run (a check, a fork) when its answer does not depend on that run. Never answer a product, cost or risk choice yourself, except as a pending decision: an owner question unanswered for `sdd.owner_wait_minutes` (default 10) does not stop the step. Notify the owner once through the runtime's push tool, if it has one; continue on the marked recommendation and write the choice as a line of its own, `[DECISION] pending owner: <option> (asked YYYY-MM-DD HH:MM UTC)`, in the artifact it shapes; finish this step and the next ones of the chain in the same branch, and stop before the merge. The spec PR lists every pending decision first; the owner's answer approves them, and each approved line is rewritten to `[DECISION] <option>, chosen by the owner on YYYY-MM-DD` (the one edit the fold rule below allows, since only that form drops the marker), then folded as usual, or changes one, which is reworked before the merge. Never merge with a pending decision: `check_spec.py` fails the line (rule `pending-decision`, KIT-113). A technical question waits for `sdd-plan`.

Put each answer where it belongs (REQ, NEED, glossary), never in an answers section, and record `YYYY-MM-DD clarify: <question> → <answer>` in the NEED's History. An answer that settles a FEAT's open `[DECISION]` amends the REQ and folds that line with the profile's `decision_folding.marker` (`sdd-plan` § 5). A vague quantity becomes a number or a `[HYPOTHESIS]` with its measurement method. An answer that reveals a new Situation returns the NEED to `sdd-specify` part 2.

## 3. Record and check

- Fill the NEED's Refinement table (one row per Situation: what it became and why) and its `requirements`, `journeys`, `processes` and `decisions` fields.
- Run the project spec validator, `CHECK_SPEC` (and `TRACE check` when journeys or processes exist; it accepts a step's `—` while an open NEED lists its journey or process), then `sdd-check NEED-nnn` (functional scope, with `TRACE similar` for C20 and C22, and `base=<merge-base commit>` with `base-diff=<git diff --unified=0 base..HEAD -- spec_root>` so it can list drift as `Pre-existing`; for a re-run after fixes also the previous run's checked `HEAD` as `since=` with its `since-diff=`; `../sdd-check/references/pre-existing.md`). A critical or high finding goes back to the step that owns it. A finding that `sdd-check` lists under `Pre-existing` (drift this NEED did not write, with base-commit evidence) does not block and is never fixed inside this NEED: route it by `sdd-intake` § 4 (a fix row, a spec fix or one owner question), a NEED of its own only when § 4 sends it there (a need or an owner decision); this NEED names the fix row or spec PR that takes it in Out of scope, or in Constraints when its delivery waits for it.

## 4. Close

With no open question, a clean functional check and product's approval of the REQs, journeys, processes and decisions: set the REQs `approved`, the journeys, product processes and product decisions `approved` (a tech process: its owner team), the NEED `refined` (a `decision` NEED with no FEAT: `delivered`, since its approved decision is the delivery; one that came from a finding first routes its answer by `sdd-intake` § 4 and names the row or PR in its History), and add `YYYY-MM-DD clarify: refined` (or `delivered`) to its History.

## Rules

- One behavior or quality per REQ; amend an existing REQ instead of writing a second one for the same behavior.
- No algorithm, message, table or framework in a REQ, a journey or a `kind: product` process (the register, `sdd-check` C11 and C26); no FEAT, debt or task row in this step.

Done when: every Situation maps to a REQ, a journey or process step, a decision or a cut; no clarification marker remains; the functional check is unblocked; and the NEED validates as `refined` with its links filled.
