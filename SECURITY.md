# Security policy

## Reporting a vulnerability

This repository is private. Report a suspected vulnerability privately; never in a public place.

1. Tell the maintainer, @ChristianPrzybulinski, directly: say what is affected and how to reproduce it.
2. You may also open an issue in this repository titled `Security: <short summary>`. It is visible to the
   repository's collaborators only. Keep exploit details, tokens, passwords and personal data out of the issue.
3. A credential that leaked (a token, a password, a key) is rotated first, before any other work; then report it.

You get an answer within 7 days. A fix is made on `main` and noted in `CHANGELOG.md` without exploit detail.

## Supported versions

Only the latest release (`VERSION`, currently the 11.x line) and `main` receive fixes.

## In scope

- the guard and format hooks (`plugins/core/hooks/`) letting a destructive or secret-leaking command through;
- the install and sync tools (`platforms/tools/*.sh`) writing outside their destinations, following a symlink
  out of the target, or touching a file they do not own;
- a skill, rule or template that instructs an agent to expose secrets or to disable a safety check.
