---
description: Always/never constraints for governed documents under docs/spec; procedures stay in the sdd-* skills.
trigger: glob
globs:
  - "docs/spec/**/*.md"
paths:
  - "docs/spec/**/*.md"
---

Always/never for governed documents under `docs/spec`. Procedures: the `sdd-*` skills and `sdd-constitution/references/sdd-process.md`.

- Always: start from the governed template (`spec-need.md`, `spec-feature.md`, `spec-requirement-functional.md`, `spec-requirement-non-functional.md`, `spec-decision.md`, `spec-debt.md`, `spec-task.md`, `spec-index.md`) and keep every section.
- Never: compress, summarize or drop a template section.
- Always: ids namespaced and sequential (`NEED-nnn`, `FEAT-nnn`, `REQ-F-nnn`, `REQ-NF-nnn`, `DEC-nnn` or the prefixes `spec.md` `decision_kinds` declares, `DEBT-nnn`, `TASK-nnn`), the file name carries the id, and a retired id is never reused.
- Always: every claim tagged `[FACT]` (with source), `[DECISION]`, `[PROPOSAL]`, `[HYPOTHESIS]` or `[BLOCKER]`; an untagged assertion counts as `[HYPOTHESIS]`.
- Always: each REQ lists the FEATs that implement it and they list it back; a REQ no FEAT implements yet is listed by an open NEED (not delivered, rejected, merged, routed or parked); a one-sided or missing link fails `check_spec.py`.
- Never: list a NEED in the link fields of a REQ, FEAT, decision or debt; a NEED's links are written only in the NEED, and the others cite it only as provenance (`source`, Rationale, History).
- Never: edit a `status` field or a task row's `Status` by hand when the repo's tooling derives it from GitHub or a `TASK-nnn` file; otherwise only the architect edits it and the PR says why.
- Always: one FEAT per delivery, never a bucket FEAT; its task rows point to `Plan § <section>` instead of restating the Plan, and are cut only after their table is approved or merged.
- Never: add an entry to `docs/spec/baseline.json` or raise a count; old findings only leave it.
- Always: prose and frontmatter in English, dates as `YYYY-MM-DD`; only a NEED's verbatim Request quote keeps the asker's language.
- Always: open only the FEAT/REQ/DEC/DEBT files the task cites and orient with `docs/spec/spec.md`; never bulk-read the corpus.
- Always: run the project spec gates (`check_spec.py`, and `spec_trace.py check` when present) and paste the literal result.
