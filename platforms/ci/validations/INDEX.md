# validations/ — validation scripts

| File | Scope | Called by |
|---|---|---|
| `check_kit.py` | kit invariants (layout, frontmatter, indexes, links, lock, duplication, compact prompt) | `platforms/tools/check.sh`, the kit's CI |
| `hook_guard_cases.json` | blocked/allowed command cases for the PreToolUse guard | `check_kit.py` |
| `hook_post_edit_cases.json` | payload/stub-tool cases for the PostToolUse format and lint hook | `check_kit.py` |
| `hook_session_start_cases.json` | throwaway-`HOME` cases for the SessionStart synced-folder warning | `check_kit.py` |
| `check_spec.py` | a project's `docs/spec/` (frontmatters and `progress/*.json`) against `../schemas/` | `check.sh --spec`, the projects' spec-lint workflow |
| `test_check_spec.py` | `check_spec.py` FEAT↔REQ cross-check and progress files (unittest) | the kit's CI |
| `spec_trace.py` | a project's `docs/spec/journeys/` traceability (journeys↔REQ↔FEAT↔tests) and `traceability.md` | project CI, copied by `sync-project.sh` when `docs/spec/journeys` exists |
| `test_spec_trace.py` | `spec_trace.py` (unittest) | the kit's CI |
| `pr_gates.py` | the no-model PR gates against the GitHub REST API | `platforms/kits/github/workflows/pr-contract.yml`, a project's review loop |
| `test_kpi.py` | `kpi.py` metrics on a fixture ledger (unittest) | the kit's CI |
| `test_sync_project.py` | `sync-project.sh --check` stale-kit-path scan on a throwaway repo (unittest) | the kit's CI |
| `test_bump_version.py` | `bump_version.py` bump, refusals and `--notes` parity with `release.yml` on a throwaway copy (unittest) | the kit's CI |
| `test_gen_index.py` | `gen_index.py` rows, invocation column, skipped entries, stale detection, a new plugin and unreadable frontmatter on a throwaway kit, plus freshness of the checked-in indexes (unittest) | the kit's CI |
| `test_complexity.py` | `complexity.py` CRAP and CC on a fixture JaCoCo XML, a fixture `.gd` pair and a stub `gdradon` in a throwaway repo (unittest) | the kit's CI |
| `test_gd_duplicates.py` | `gd_duplicates.py` pairs, size minimums, strings-only pairs, threshold, parse failures, cache and missing gdtoolkit on fixture `.gd` files in a throwaway repo (unittest; the parser cases skip without gdtoolkit) | the kit's CI |
