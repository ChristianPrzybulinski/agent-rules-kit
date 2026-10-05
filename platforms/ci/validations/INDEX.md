# validations/ — validation scripts

| File | Scope | Called by |
|---|---|---|
| `check_kit.py` | kit invariants (layout, frontmatter, indexes, links, lock, duplication, compact prompt) | `platforms/tools/check.sh`, the kit's CI |
| `hook_guard_cases.json` | blocked/allowed command cases for the PreToolUse guard | `check_kit.py` |
| `check_spec.py` | a project's `docs/spec/` against `../schemas/` | `check.sh --spec`, the projects' spec-lint workflow |
| `test_check_spec.py` | `check_spec.py` FEAT↔REQ cross-check (unittest) | the kit's CI |
