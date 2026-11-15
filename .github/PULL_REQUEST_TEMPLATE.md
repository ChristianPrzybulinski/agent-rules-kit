## Checklist

- [ ] `platforms/tools/check.sh` and `platforms/tools/smoke.sh` passed locally (on macOS they also parse the scripts with bash 3.2, which the runner cannot), and `gitleaks git --redact --log-opts="origin/main..HEAD"` was clean before the push
- [ ] The required checks `ci`, `workflow-lint`, `gitleaks`, `codeql (python)` and `codeql (actions)` are green on this head; the merge also needs an independent review READY (KIT-076)
- [ ] `python3 platforms/tools/gen_index.py` run if a skill, rule, template, agent, eval or hook changed (plugin `INDEX.md` files are generated)
- [ ] `CHANGELOG.md` updated (visible change)
- [ ] A `docs/features/KIT-NNN` record and its `kit-feature` issue exist only if this PR changes a hook, `plugins/guardrails/AGENTS.md`, plugin structure or manifests, a check, gate or script behavior, or adds or removes a skill; otherwise the PR body says why
- [ ] No folder or install destination changed (10.x layout frozen; see docs/design.md "Layout stability"); if one did, this PR is MAJOR with a deprecation note and a doctor.sh migration
- [ ] `VERSION` bumped per SemVer if this is a release

## What changes

<!-- 1-3 lines -->
