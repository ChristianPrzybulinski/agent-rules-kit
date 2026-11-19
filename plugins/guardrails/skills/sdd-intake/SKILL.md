---
name: sdd-intake
description: "SDD entry — a request becomes a NEED-nnn; a finding is routed by type. Use when a request arrives or work finds a defect. Not for triage (skill sdd-specify)."
argument-hint: "<request in natural language> | <finding with its evidence>"
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

Two entries (KIT-104). A request someone makes (an idea, a need, an improvement, a problem they report) becomes a `NEED-nnn` under `docs/spec/needs/` with `status: proposed` (§§ 1–3); that part only records: it never judges, classifies or prioritizes, and it reads nothing beyond `docs/spec/needs/` and `docs/spec/spec.md`. A finding that work turns up is routed by the agent that found it (§ 4) and becomes a NEED only where § 4 says so: a NEED is a need someone asks for, or a decision only the product owner can make. Process: `../sdd-constitution/references/sdd-process.md`. Template: `../../templates/spec-need.md`.

Resolve the project profile first (`../session/references/project-profile.md`): `spec_root` (every `docs/spec` here) and `sdd`. With `sdd.needs: false` (`../sdd-constitution/references/sdd-parameters.md`) the project keeps no NEED file: skip §§ 1–3 and hand the request, quoted verbatim with its date and channel, to `sdd-specify`; § 4 applies as written.

## 1. Take the id

- Take the next unused `NEED-nnn` in `docs/spec/needs/`, or the first unused id of the block the session prompt reserves.

## 2. Write the record

- Create `docs/spec/needs/NEED-nnn.md` from the template, keeping every section.
- Fill only the title, a provisional `type`, `origin`, the Request quote (verbatim, in the asker's language, with date and channel) and one line of Problem / value; a report handed over by `investigate` or `sdd-spike` is cited in Evidence. Every other section holds `—`.
- A request holding several needs becomes one NEED each: the first records the request and lists the others, and each of them sets `parent` to it.
- Add the History line `YYYY-MM-DD intake: created from <channel>.`

## 3. Validate and hand off

- Run the spec validator (`CHECK_SPEC`; in this kit, `platforms/tools/check.sh --spec docs/spec`) and paste its literal output.
- Hand the NEED to `sdd-specify`, now or later; a recorded NEED may wait.

## 4. Route a finding where it is found

A finding is a defect or gap that work turns up: an audit (`sdd-check all` included), `sdd-check` on drift the change under check did not write, `sdd-review`, `sdd-release` acceptance, smoke or production, `investigate`, a security scan, a migration. The agent that found it routes it where it is found, by type, first match wins, with its evidence (`path:line`, the failing output):

| Type | Rule | Route |
|---|---|---|
| fix | a REQ, journey, process or decision states the right behavior and the code differs, or nobody would choose what the code does (a crash, lost data, a red check) | a fix task row on the FEAT that owns the code, citing the violated artifact's path and the evidence (where it goes: the Fix row bullet) |
| spec fix | the spec text is stale or silent, and another approved artifact or a recorded owner decision already states what the code does, so restating it changes nothing the actor experiences | fixed in the same change, or in the next spec PR of that area, whose body lists each spec fix with its finding for product to review; an amended REQ, journey or process takes a History line naming the finding and the artifact or answer it now follows, an approved decision changes only with the owner's yes (`owner_approvals`), and a new REQ joins the FEAT that owns the code as a fix does, with `status: proposed` (it becomes `approved` only through `sdd-clarify` § 4, with product's approval) |
| product choice | the code and an artifact disagree on what the actor experiences, or no artifact or owner decision states what the code does, and either could be right | one question to the product owner with a concrete example and a recommendation (`sdd-clarify` § 2); the answer becomes a fix row or a spec fix. Only a choice that needs more than one question, or one still unanswered when the session ends, becomes a NEED of type `decision` (§§ 1–3), whose approved answer this table routes again; that NEED names the row or PR that takes it |
| new capability | someone needs what no REQ, journey or process covers | a NEED (§§ 1–3), the need and who has it in its Request |

- Fix row: the owning FEAT is the one whose rows' Files hold the path; when the rows of several FEATs hold it, the FEAT with an open block first, else the most recently delivered one; with no row holding it, the one that implements the violated REQ. The report names the choice. A `planned`, `in-progress` or `validated` FEAT takes the row in its table (its open block with `## Versions`), with a History line naming the row and the defect; a `validated` FEAT first goes back to `in-progress` through `TRACE status --write` once the row is open (as `sdd-release` § 4 does). Then the row check (`sdd-tasks` § 3, `sdd-check` C17) runs and `sdd-tasks FEAT-nnn resync` cuts the row. A FEAT or block not yet planned takes the row when `sdd-plan` plans it. A delivered FEAT takes it in its next version block, and code no FEAT owns in a new FEAT, both opened by `sdd-plan` § 1 with no NEED.
- With `sdd.flow: feat-only` (no task table, KIT-100) a fix is its own PR, with a FEAT only when it is big (`sdd.record_when`). Where the project keeps no NEED file (`sdd.needs: false`, or feat-only), a new capability is a request handed to `sdd-specify` (feat-only: an issue for `sdd-plan`), and a product choice that would become a `decision` NEED is an issue, so it stays recorded; with `tracker: none` it is a note in the project's collaboration folder (as `sdd-spike` § 4 does), cited in the report.
- The report that found it (the audit, the closure record, the release PR, the `investigate` report) names each finding's route and the row, PR or question that took it.

## Rules

- Never change the meaning of the Request quote, and never write a REQ, FEAT, decision, debt or task row in §§ 1–3.
- Capture costs one file, so a request is recorded before anyone judges it; a finding costs no file, since its finder already judged it with evidence.

Done when: the NEED validates with `status: proposed`, its Request is verbatim and every section the step does not fill holds `—`; or each finding names its route and the row, PR or question that took it.
