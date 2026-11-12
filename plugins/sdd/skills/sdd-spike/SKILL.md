---
name: sdd-spike
description: Prototype lane for game feel. Use when movement, camera, battle feedback or UI must be felt on screen before a FEAT exists. Not for specs (skill sdd-specify).
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

The question must be about feel (movement, camera, battle feedback, UI) and unanswerable by reading the spec. If a FEAT already specifies it, stop and use `sdd-implement`.

## 2. Open the lane

- `git switch -c spike/<topic>` from updated `main`.
- `max-days` defaults to 2 and never exceeds 2.
- Record the question and the end date in an empty first commit: `git commit --allow-empty -m 'chore(spike): open spike/<topic>, question: ..., ends YYYY-MM-DD'`. No file is added and nothing under `docs/spec/` changes.
- Open an issue for the spike if none exists; the deliverables are posted there.

## 3. Rules while spiking

- No file under `docs/spec/` changes.
- No coverage, lint, mutation or `validate-implementation` gate applies; any code shape is allowed.
- Measure what the question asks (frame time, input-to-motion latency, tile crossing time, hit-feedback delay) and record the numbers.

## 4. Deliver

- Post a GIF, video or screenshot set and the filled `doc-spike-report.md` as comments on the spike's issue, never under `docs/spec/`.
- Never open a PR from `spike/<topic>`. If media hosting forces a PR, open it as a draft titled `spike: <topic> (do not merge)` and close it unmerged right after the report.
- When a product choice emerged, write a proposed `DGME-nnn` or `DTEC-nnn` from `../../templates/spec-decision.md` with `status: proposed`; the user opens it as a normal docs PR.

## 5. Close the lane

The spike branch never merges to `main`. After the report, ask the user to either delete it (`git branch -D spike/<topic>` and `git push origin --delete spike/<topic>` are the user's commands, never yours) or re-implement the kept idea through `sdd-specify`, then `sdd-plan`, `sdd-tasks` and `sdd-implement`; the report's keep list is the input to `sdd-specify`.

Done when: the question has a measured answer, the report and media are posted, any decision is a proposed DGME/DTEC, and the spike branch is deleted or scheduled for re-implementation.
