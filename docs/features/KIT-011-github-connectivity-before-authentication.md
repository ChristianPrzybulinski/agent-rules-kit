---
id: KIT-011
title: "Distinguish GitHub connectivity failures from authentication"
status: done
confirmed: "2026-10-24 (owner, Codex GitHub connectivity diagnosis chat; exact skill text approved)"
issue: "#90"
pr: "#91"
---

# KIT-011 — Distinguish GitHub connectivity failures from authentication

## Problem and evidence

[FACT] On 2026-10-24, in stratics-docs at commit
`4e64d335a9c31cf25892525cfb324ab1ce209184`, these reads failed inside the Codex sandbox:

```sh
gh pr view 2602 --repo ChristianPrzybulinski/stratics-docs --json headRefOid,baseRefOid,state
git ls-remote origin refs/heads/main
```

The errors were `error connecting to api.github.com` and `Could not resolve host: github.com`.
Both commands succeeded with per-command sandbox escalation. The GitHub connector also read PR metadata.
An independent Python DNS check failed for both hosts inside the sandbox and succeeded outside it.
This establishes the cause of that episode, not every previous GitHub access failure.

## Change

- `plugins/infra-github/skills/github-cli/SKILL.md`: preserve the owner-approved text distinguishing
  connectivity from invalid authentication, using a supported connector read or narrowly scoped escalation,
  and reconciling ambiguous mutations before retrying. One exact instruction is:
  "A permission or rate-limit error alone does not justify logging in again."
- `plugins/infra-github/evals/`: three cases for network fallback, authentication evidence and ambiguous mutations.
- `plugins/infra-github/INDEX.md`, this feature index and `CHANGELOG.md`: record the cases and correction.

## Proof

The implementation session passed:

```sh
platforms/tools/check.sh --links
CI=1 platforms/tools/check.sh --links
platforms/tools/smoke.sh
python3 -B -m unittest discover -s platforms/ci/validations -p 'test_*.py'
shellcheck platforms/tools/*.sh platforms/kits/*/*.sh platforms/kits/*/scripts/*.sh
git diff --check
```

The unit suite reported 65 tests with one skip because `SPEC_TRACE_CORPUS` was not set.
Evaluation prompts and graders were parsed, but model-driven evaluations were not executed.

## History

- 2026-10-24: owner approved the exact correction, then authorized its PR and merge; implementation validated locally.
- 2026-10-24: implementation recorded in PR #91; model-driven evaluations remain unexecuted.
