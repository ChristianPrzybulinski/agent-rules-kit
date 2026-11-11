---
id: KIT-028
title: "A state file names the session writing its worktree"
status: confirmed
confirmed: "2026-11-11 (owner, chat of the Stratics audit roadmap prompt session: \"sim para o kit\")"
issue: "#130"
pr: ""
---

# KIT-028 — A state file names the session writing its worktree

## Problem and evidence

[FACT] On 2026-11-10 at 21:24 (-03) the continuation prompt `/Users/christian/Developer/GitHub/PROMPT-AUDIT-ROADMAP-2026-11-10.md`
was opened in a new session while the Stratics session "Audit roadmap specification PR" was still writing the same worktree,
`/Users/christian/Developer/GitHub/wt-audit-roadmap`: `docs/spec/features/FEAT-110.md` had been modified at 21:23:47, and that
session's last message reported its gates green.

[FACT] The state file `/Users/christian/Developer/GitHub/AUDIT-ROADMAP-STATE-2026-11-10.md` recorded the amendment approval
and "Next: FEAT-110", but not that FEAT-110 was being written or by which session. Only file modification times and the
session list showed the conflict; the prompt's step 1 asked to confirm that no other session writes in the worktree, with no
record to check against.

## Change

`plugins/core/skills/session/SKILL.md` § start gains one bullet:

> Before the first edit in a worktree or folder that a state or handoff file describes, read that file's top line
> `Writer: <session id> since <YYYY-MM-DD HH:MM>`. A line naming another session that is still running means stop and ask
> the user; never write beside it. Otherwise add the line before the first edit and remove it at close or handoff.

`CHANGELOG.md` `[Unreleased]` records it. No change to `VERSION`.

## Proof

`bash platforms/tools/check.sh`; `bash platforms/tools/smoke.sh`; `python3 platforms/ci/validations/check_kit.py --links`;
`gitleaks git --redact --log-opts="origin/main..HEAD"`.

## History

- 2026-11-11: confirmed (owner, chat); issue #130 opened.
