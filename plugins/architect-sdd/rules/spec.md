---
description: Always/never constraints for governed documents under docs/spec; procedures stay in the sdd-* skills.
trigger: glob
globs:
  - "docs/spec/**/*.md"
paths:
  - "docs/spec/**/*.md"
---

Always/never for governed documents under `docs/spec`. Procedures: the `sdd-*` skills and `sdd-constitution/references/sdd-process.md`.

- Always: start from the governed template (`spec-feature.md`, `spec-requirement-functional.md`, `spec-requirement-non-functional.md`, `spec-decision.md`, `spec-debt.md`, `spec-index.md`) and keep every section.
- Never: compress, summarize or drop a template section.
- Always: ids namespaced and sequential (`FEAT-nnn`, `REQ-F-nnn`, `REQ-NF-nnn`, `DTEC-nnn`/`DGME-nnn`/`DPRO-nnn`, `DEBT-nnn`), the file name carries the id, and a retired id is never reused.
- Always: every claim tagged `[FACT]` (with source), `[DECISION]`, `[PROPOSAL]`, `[HYPOTHESIS]` or `[BLOCKER]`; an untagged assertion counts as `[HYPOTHESIS]`.
- Always: a FEAT lists its REQs and each REQ lists that FEAT; a one-sided link fails `check_spec.py`.
- Never: edit a `status` field by hand when the repo's tooling derives it from GitHub; otherwise only the architect edits it and the PR says why.
- Always: prose and frontmatter in English, dates as `YYYY-MM-DD`.
- Always: open only the FEAT/REQ/DEC/DEBT files the task cites and orient with `docs/spec/spec.md`; never bulk-read the corpus.
- Always: run the project spec gates (`check_spec.py`, and `spec_trace.py check` when present) and paste the literal result.
