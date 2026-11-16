## Checklist

- [ ] Locally only the TDD loop (the tests covering the changed files) and the linters: `platforms/tools/check.sh` passed (on macOS it also parses the scripts with bash 3.2, which the runner cannot), `platforms/tools/smoke.sh` too when a script it runs changed, and `gitleaks git --redact --log-opts="origin/main..HEAD"` was clean before the push; CI runs the rest
- [ ] A change to a skill or a rule: the evals ran by hand before this PR, and the body has an `Evals:` line with the command and the score (`.github/CONTRIBUTING.md` § Evals)
- [ ] The required checks `ci`, `workflow-lint`, `gitleaks`, `codeql (python)`, `codeql (actions)` and `CodeQL` (code scanning results) are green on this head; the merge also needs an independent review READY (KIT-076)
- [ ] `python3 platforms/tools/gen_index.py` run if a skill, rule, template, agent, eval or hook changed (plugin `INDEX.md` files are generated)
- [ ] `CHANGELOG.md` updated (visible change)
- [ ] A `docs/features/KIT-NNN` record and its `kit-feature` issue exist only if this PR changes a hook, `plugins/guardrails/AGENTS.md`, plugin structure or manifests, a check, gate or script behavior, or adds or removes a skill; otherwise the PR body says why
- [ ] No folder or install destination changed (10.x layout frozen; see docs/design.md "Layout stability"); if one did, this PR is MAJOR with a deprecation note and a doctor.sh migration
- [ ] `VERSION` bumped per SemVer if this is a release

## What changes

<!-- 1-3 lines -->
