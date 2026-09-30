# validations/ — validation scripts

| File | Scope | Called by |
|---|---|---|
| `check_kit.py` | kit invariants (layout, frontmatter, indexes, links, lock, duplication, compact prompt) | `platforms/tools/check.sh`, the kit's CI |
| `check_spec.py` | a project's `docs/spec/` against `../schemas/` | `check.sh --spec`, the projects' spec-lint workflow |
