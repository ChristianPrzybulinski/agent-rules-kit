# validations/ — validation scripts

| File | Scope | Called by |
|---|---|---|
| `check_kit.py` | kit invariants (layout, frontmatter, indexes, links, lock, duplication, compact prompt) | `platforms/tools/check.sh`, the kit's CI |
| `hook_guard_cases.json` | blocked/allowed command cases for the PreToolUse guard | `check_kit.py` |
| `hook_post_edit_cases.json` | payload/stub-tool cases for the PostToolUse format and lint hook | `check_kit.py` |
| `check_spec.py` | a project's `docs/spec/` against `../schemas/` | `check.sh --spec`, the projects' spec-lint workflow |
| `test_check_spec.py` | `check_spec.py` FEAT↔REQ cross-check (unittest) | the kit's CI |
| `spec_trace.py` | a project's `docs/spec/journeys/` traceability (journeys↔REQ↔FEAT↔tests) and `traceability.md` | project CI, copied by `sync-project.sh` when `docs/spec/journeys` exists |
| `test_spec_trace.py` | `spec_trace.py` (unittest) | the kit's CI |
| `pr_gates.py` | the no-model PR gates against the GitHub REST API | `platforms/kits/github/workflows/pr-contract.yml`, a project's review loop |
| `test_sync_project.py` | `sync-project.sh --check` stale-kit-path scan on a throwaway repo (unittest) | the kit's CI |
