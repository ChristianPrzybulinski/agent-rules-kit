---
name: sdd-spike
description: Prototype lane for feel or feasibility. Use when motion, UI feel or a technical risk must be tried in code before a FEAT. Not for specs (skill sdd-intake).
argument-hint: "[topic] [max-days]"
triggers:
  - user
disable-model-invocation: true
allowed-tools:
  - read
  - grep
  - glob
  - exec
  - edit
---

# SDD lane: Spike

Process: `../sdd-constitution/references/sdd-process.md`. Report template: `../../templates/doc-spike-report.md`.

## 1. Qualify

Resolve the project profile first (`../session/references/project-profile.md`): `spec_root` and `stacks`.

The question must be about feel (motion, camera, feedback, UI) or technical feasibility (a load-bearing risk `sdd-plan` names whose cheapest test needs code), and unanswerable by reading the spec. If a FEAT already specifies it, stop and use `sdd-implement`.

## 2. Open the lane

- `git switch -c spike/<topic>` from updated `main`.
- `max-days` defaults to 2 and never exceeds 2.
- Record the question and the end date in an empty first commit: `git commit --allow-empty -m 'chore(spike): open spike/<topic>, question: ..., ends YYYY-MM-DD'`. No file is added and nothing under `docs/spec/` changes.
- Name where the deliverables go: the spike's issue when the project uses a tracker, otherwise the NEED it serves (a new one through `sdd-intake` when none exists).

## 3. Rules while spiking

- No file under `docs/spec/` changes.
- No coverage, lint, mutation or `review` gate applies; any code shape is allowed.
- Measure what the question asks (frame time, input-to-motion latency, tile crossing time, hit-feedback delay; throughput, memory or latency for a feasibility risk) and record the numbers.

## 4. Deliver

- Post a GIF, video or screenshot set and the filled `doc-spike-report.md` on the spike's issue; without a tracker, keep them in the project's collaboration folder and cite them in the NEED's Evidence. Never put them under `docs/spec/`.
- Never open a PR from `spike/<topic>`. If media hosting forces a PR, open it as a draft titled `spike: <topic> (do not merge)` and close it unmerged right after the report.
- When a product choice emerged, write a proposed decision record from `../../templates/spec-decision.md` with `status: proposed`; the user opens it as a normal docs PR.

## 5. Close the lane

The spike branch never merges to `main`. After the report, ask the user to either delete it (`git branch -D spike/<topic>` and `git push origin --delete spike/<topic>` are the user's commands, never yours) or re-implement the kept idea through the chain: the NEED it served (or a new one from `sdd-intake`) cites the report as Evidence, and its keep list is the input to `sdd-specify`.

Done when: the question has a measured answer, the report and media are posted, any decision is a proposed decision record, and the spike branch is deleted or scheduled for re-implementation.
