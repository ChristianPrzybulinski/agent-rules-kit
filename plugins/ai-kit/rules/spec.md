---
description: Load governed specification templates and SDD skills for files under docs/spec.
trigger: glob
globs:
  - "docs/spec/**/*.md"
paths:
  - "docs/spec/**/*.md"
---

Governed documents: use `templates/spec-*.md` and the `sdd-*` skills.
Never compress these documents.
