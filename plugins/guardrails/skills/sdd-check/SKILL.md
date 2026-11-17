---
name: sdd-check
description: SDD tool — read-only spec check that sdd-clarify and sdd-plan call. Use when a NEED, a FEAT or the spec needs gap checks. Not for ambiguity (skill sdd-clarify).
argument-hint: "NEED-nnn | FEAT-nnn | all [validator=<output of check_spec.py 2>&1>] [trace=<output of spec_trace.py check 2>&1>] [rows=<output of the row check 2>&1>] [enablers=<output of spec_trace.py enablers 2>&1>]"
triggers:
  - user
  - model
agent: researcher
context: fork
background: false
allowed-tools:
  - read
  - glob
  - grep
---

# SDD tool — Check

Process: `../sdd-constitution/references/sdd-process.md`. Read-only: this tool edits no specification. It is not a step of the chain: `sdd-clarify` and `sdd-plan` call it before their status move, and anyone may run it as an audit. Checklist: `references/check-list.md`.

Scope, chosen by the argument:
- functional (`NEED-nnn`, called by `sdd-clarify` before `refined`): the NEED, its REQs, journeys, processes and product decisions; rows C1, C2, C4, C5, C6, C11, C12, C13, C14 (range, unit and exposure), C26, the journey and process links and checklist Q1 (read against each REQ's Verification), Q2–Q4, Q7 and Q12; a block stops `refined`.
- full (`FEAT-nnn`, called by `sdd-plan` before `planned`): the functional scope again on the FEAT's REQs and its NEED, plus the FEAT, its Plan, Tasks once cut and decisions with rows C3, C7, C8, C9, C10, the task cut and decision folding (§ 1 d, e), C14 (exposure), C15, C18 and C19 (with `docs/spec/enablers/`) and checklist Q1 (read against the FEAT's criteria), Q5, Q6 and Q8–Q11; a block stops `planned`.
- With `sdd.needs: false` (no NEED file) there is no functional run: the full scope reads the FEAT's Problem section where it reads the NEED (C1 checks the FEAT→REQ link and a Problem Situation with no REQ).
- With `sdd.flow: feat-only` (KIT-100: no NEED and no REQ) only the full scope runs, on the FEAT alone: C1 and C8 read each Scope line against an acceptance criterion and each criterion against its `Proof` command instead of the REQ links, and the REQ rows (C11, C12, C13, C14, C18, C26, Q12) and § 1 b do not apply.
- `all` (an audit): the full scope on every artifact. `docs/spec/baseline.json` may hold old findings per row (`C<n>`, `Q<n>`) and artifact id with a count: a finding within its count is listed under `Baseline` and does not block; one above it, or on an artifact the file does not hold, is reported as usual; an entry that finds less than its count is listed as `lower: <row> <artifact> <count> → <found>`. The file only shrinks: never propose adding an entry (`check_spec.py` keeps its own rows the same way).

## 1. Mechanical checks

Resolve the project profile first (`../session/references/project-profile.md`): `spec_root` (every `docs/spec` here) and `sdd`; the commands below are its § 3 names.

a. Validator verdict. The calling session runs `CHECK_SPEC 2>&1` (the installed kit's validator) and pastes the whole output after `validator=`, because the `researcher` profile has no `exec`. Success is the line `spec: OK (N artifacts)`, with `; M findings held by baseline.json` when `docs/spec/baseline.json` holds old findings; failures are `FAIL: ...` lines on stderr, hence `2>&1`. With no `validator=` argument, finding #1 is `high | validator not run; run <command>`. Every pasted `FAIL:` line becomes one `high` finding; a `BASELINE:` line or a `WARN:` line is not a finding (a `WARN` on task size or a long Task cell goes in the report's notes).

b. Journey and process links (functional and full scope, only when the project keeps journeys: `sdd.journeys`, absent = on when `docs/spec/journeys/` exists, or `docs/spec/enablers/` exists, whose ENB table checks run here too). The calling session pastes `TRACE check 2>&1` after `trace=`; each failure line is one `high` finding, and a missing `trace=` is `high | journey check not run`. A step written in `sdd-clarify` holds `—` in `Implemented by` and `Proven by`, which the validator accepts while an open NEED lists the journey in `journeys`, and its listed FEATs have not yet all delivered every REQ it lists (`../sdd-clarify/references/journeys.md`), so a NEED's new step does not block `refined`. A step that cites `PROC-nnn` or `PROC-nnn S<a>–S<b>` is checked through the process, which `spec_trace.py check` expands; an "as in J-nn" step with no links of its own is a `high` finding.

c. Consistency table. Load the artifacts of the scope, then check its rows:

| Id | Check | Severity |
|---|---|---|
| C1 | missing FEAT↔REQ (full) or NEED→REQ (functional) link, orphan requirement, or a NEED Situation with no Refinement row | high |
| C2 | contradictory criteria/requirements | critical |
| C3 | dependency on a lower-status feature | high |
| C4 | undefined glossary term | low |
| C5 | vague unmeasured quantity | medium |
| C6 | unclassified claim | medium |
| C7 | rejected alternative without DEC | medium |
| C8 | REQ in Scope with no criterion proving it; criterion without task or task without criterion, once Tasks exist | high |
| C9 | plan violating kit/repository rule | critical |
| C10 | invalid frontmatter | high |
| C11 | a REQ states how instead of what (algorithm, message, table, framework); rule: `../sdd-clarify/references/req-scope.md` | medium |
| C12 | a process state with no exit (unless the Postconditions name it final), a state that neither the Trigger, a step nor another state enters, a decision point without a row per outcome, or a step whose rule is prose instead of a REQ id; rule: `../sdd-clarify/references/processes.md` § Soundness | high |
| C13 | a NEED that names no pillar (`new`, `improvement`, `content` or `decision`) or a pillar `spec.md` does not list, while `spec.md` has `## Pillars`; or a NEED that matches a `spec.md` Out of scope line and is not closed `rejected` or `parked` citing it; rule: `../sdd-specify/SKILL.md` § 1 | high |
| C14 | a REQ-F Values row whose `Tunable` cell is empty, or neither `fixed` nor a range with its unit and exposure; in the full scope, a non-`fixed` tunable of the FEAT's REQs with no line in Plan § Data naming where it is exposed (content key, config, a debug control); rule: `../sdd-clarify/references/req-scope.md` § 1 | medium |
| C15 | a Plan § Assets row without its source, its license or the REQ or mock it serves (full scope); rows: `../sdd-plan/references/plan-sections.md` | medium |
| C18 | a REQ of the FEAT, or a process step whose Rules cite REQs, that no ENB satisfies in its Aggregates or Qualities (full scope, with `docs/spec/enablers/`); tool: § 1 f | high |
| C19 | a Plan § Contract reference `ENB-nnn:<contract>` the catalog lacks or to an ENB the FEAT's `enablers` omits, or a protocol schema or migration no ENB `Schema or file` cell covers; a provided contract with no consumer and no `public` mark; tool: § 1 f | high; medium for no consumer |
| C26 | technical text (a solution, framework, table, endpoint, class, file path, engine call or message format) in a NEED, a journey's or a `kind: product` process's action, result or state cells, or a decision whose kind is not technical; aid: grep the scope for `endpoint`, `table`, `class`, `JSON`, `SQL`, `.gd`, `.java` and rooted paths, then judge each hit (`Implemented by` and `Proven by` hold links and are exempt); rule: `../sdd-constitution/references/sdd-process.md` § Register, the process row `../sdd-clarify/references/processes.md` § Write | medium |

d. Task cut (full scope, while the FEAT has rows not yet `done` or `cancelled`). The calling session pastes after `rows=` the row check's output (`row_check`, else `ROWS check FEAT-nnn`) and the `task_cut` block of `PROFILE resolve --section sdd`; each `FAIL` line is one `high` finding, a `WARN` goes in the notes, and a missing `rows=` is `high | row check not run`. Then read each row against `../sdd-tasks/references/task-cut.md` with those values: an owned area outside `owned_area_form`, a code path without its `required_test_folders`, a protected path whose item lacks its label, a hotspot edited where an additive registry fits, an ordering-only `Depends on` edge, a row on the longest chain above `longest_chain_max_complexity`, or a bundled item holding a `bundle_exclude` row is one `medium` finding each (`high` for a missing label or test folder).

e. Decision folding (full scope, on a FEAT not yet `delivered` or `cancelled`). A settled `[DECISION]` line in the FEAT's Open questions without the profile's `decision_folding.marker` and its target after the FEAT's last spec PR, a marker whose target (Scope, `CA-n`, a REQ id) does not state the decision, or a folded line listed above an unfolded one is one `medium` finding (skill `sdd-plan` § 5).

f. Enabler catalog (full scope and `all`, only when `docs/spec/enablers/` exists). The calling session pastes `TRACE enablers <spec_root> --feat FEAT-nnn 2>&1` (no `--feat` for `all`) after `enablers=` and `TRACE check <spec_root> 2>&1` after `trace=`; both run, because `enablers` prints OK while `check` fails an ENB table error such as a row missing from `providesApis`. Each `C18`/`C19` line is one finding of its printed severity and blocks by it (§ 3: high blocks, medium does not), each `check` failure one `high` finding; the tool exits 1 on any finding, a medium one included, so its exit code is not the verdict. The no-consumer and catalog-file checks read every ENB whatever `--feat` names. A missing `enablers=` is `high | enabler check not run`; a missing `trace=` is the one § 1 b finding. Protocol schemas are covered through `sdd.row_checks.protocol.schemas` and migrations through the profile's `sdd.migrations` folders; `--catalog <glob>` adds a folder the profile does not list yet.

## 2. Judgment checks

Grade every item of `references/check-list.md` that the scope covers (functional Q1–Q4, Q7 and Q12, full Q1–Q12) pass / fail / not-applicable with a `path:line` as evidence. A fail on a security or integrity item is `critical`.

## 3. Report

One format. Line one: `validator: OK (N artifacts[; M held]) | FAIL (n lines) | not run`. Then `# | step | severity | file:line | problem | suggestion`, counts by severity, and `blocked: yes|no` (critical or high blocks `refined` in the functional scope and `planned` in the full scope). Save under `docs/spec/reports/` only when requested; the calling session pastes the table into the FEAT `## Audit` section, or the NEED's History as one line with the counts.

## 4. Route findings

Ambiguity, a C12, C26 or Q12 finding and a C14 tunable without range, unit or exposure go to `sdd-clarify`, a missing Situation or a C13 finding to `sdd-specify`, a plan or task gap (a C14 tunable with no Plan § Data exposure, a C18 or a C19 included) to `sdd-plan` or `sdd-tasks`, a kit-rule violation to a decision record or a blocker.

Done when: every finding cites `path:line`, the validator verdict is on line one, and the report states its scope and whether the next status is blocked.
