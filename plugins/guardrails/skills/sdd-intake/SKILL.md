---
name: sdd-intake
description: "SDD entry — record an idea, need, improvement or problem as a NEED-nnn. Use when a request arrives. Not for classifying it (skill sdd-specify)."
argument-hint: "<request in natural language>"
triggers:
  - user
  - model
allowed-tools:
  - read
  - glob
  - grep
  - edit
  - exec
---

# SDD entry — Intake

Every request enters here and becomes a `NEED-nnn` under `docs/spec/needs/` with `status: proposed`. This skill only records: it never judges, classifies or prioritizes, and it reads nothing beyond `docs/spec/needs/` and `docs/spec/spec.md`. Process: `../sdd-constitution/references/sdd-process.md`. Template: `../../templates/spec-need.md`.

## 1. Take the id

- Take the next unused `NEED-nnn` in `docs/spec/needs/`, or the first unused id of the block the session prompt reserves.

## 2. Write the record

- Create `docs/spec/needs/NEED-nnn-slug.md` from the template, keeping every section.
- Fill only the title, a provisional `type`, `origin`, the Request quote (verbatim, in the asker's language, with date and channel) and one line of Problem / value. Every other section holds `—`.
- A request holding several needs becomes one NEED each: the first records the request and lists the others, and each of them sets `parent` to it.
- Add the History line `YYYY-MM-DD intake: created from <channel>.`

## 3. Validate and hand off

- Run the project spec validator (`python3 .github/spec-lint/check_spec.py docs/spec .github/spec-lint/schemas`; in this kit, `platforms/tools/check.sh --spec docs/spec`) and paste its literal output.
- Hand the NEED to `sdd-specify`, now or later; a recorded NEED may wait.

## Rules

- Never change the meaning of the Request quote, and never write a REQ, FEAT, decision, debt or task row in this step.
- Capture costs one file, so a request is recorded before anyone judges it.

Done when: the NEED validates with `status: proposed`, its Request is verbatim and every section the step does not fill holds `—`.
