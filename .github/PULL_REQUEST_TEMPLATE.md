## Checklist

- [ ] `platforms/tools/check.sh` passed (local, without CI=1) and passes with `CI=1` + pyyaml/jsonschema
- [ ] `platforms/tools/smoke.sh`, `python3 platforms/ci/validations/check_kit.py --links` and `gitleaks git --redact --log-opts="origin/main..HEAD"` passed locally (kit CI runs only on demand, KIT-014)
- [ ] `python3 platforms/tools/gen_index.py` run if a skill, rule, template, agent, eval or hook changed (plugin `INDEX.md` files are generated)
- [ ] `CHANGELOG.md` updated (visible change)
- [ ] A `docs/features/KIT-NNN` record and its `kit-feature` issue exist only if this PR changes a hook, `plugins/guardrails/AGENTS.md`, plugin structure or manifests, a check, gate or script behavior, or adds or removes a skill; otherwise the PR body says why
- [ ] No folder or install destination changed (10.x layout frozen; see docs/design.md "Layout stability"); if one did, this PR is MAJOR with a deprecation note and a doctor.sh migration
- [ ] `VERSION` bumped per SemVer if this is a release

## What changes

<!-- 1-3 lines -->
