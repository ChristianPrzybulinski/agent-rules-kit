---
description: Always/never constraints for JSON data, schema and config files; validators and procedures stay with the repo and the skills that own each format.
trigger: glob
globs:
  - "**/*.json"
paths:
  - "**/*.json"
---

Always/never for `*.json`. Procedures: skill `protocol-contract` for message schemas and examples; the repo `AGENTS.md` names its validators.

- Always: change only the values the task needs; keep the file's indent, key order, LF line endings, UTF-8 without BOM and its one final newline, so `git diff` shows only the intended lines.
- Never: comments, trailing commas or a duplicate key; most parsers keep one duplicate silently, so search the object for a key before adding it.
- Always: more than one value or more than one file changes through a short script (`json.load`; edit; `json.dump` with the file's indent, `ensure_ascii=False` when it holds raw non-ASCII text, and a final newline), then parse the result again and read `git diff`; a whole-file reformat is a defect.
- Never: read a multi-megabyte JSON whole into the context (a built content pack can pass 30 MB); query it with `jq` or a script and print only the fields you need.
- Never: hand-edit generated JSON (built packs, generated protocol tables, lock files); change its source, rerun the generator and its `--check`.
- Always: data validates against its schema with the validator the repo `AGENTS.md` names before "done", with its literal tail; a new data file refers to its schema the way its neighbors do.
- Always: a JSON Schema declares `$schema` (draft 2020-12 unless the repo fixes another) and an `$id` in the repo's existing style; a breaking schema change updates every instance in the same change.
- Never: rename or reuse a stable id (content, message or error id); add a new one and retire the old one as the repo's process says.
