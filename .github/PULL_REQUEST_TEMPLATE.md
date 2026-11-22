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

## Red

Test: `<file::name>` fails on base and passes on this head. If no test changed, replace this line with `Exception: <why>` (the `red` check reads the first line of this section).

<!-- A fix or perf PR, or one that closes a bug issue: replace this comment with
## Five whys
Symptom: <what failed, with the command, check or PR that shows it>
1. <why> — <evidence: file:line, log, PR, command output>
Root cause: <the why this PR removes>
Fix: <what changes, which why it removes>
Wrong if: <the observation that would show it did not>
Exempt: `Five whys: exempt (typo | test-only | docs-only | release | records)`. Five is a ceiling, not a quota. -->
