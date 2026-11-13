# Security policy

## Reporting a vulnerability

This repository is public. Report a suspected vulnerability privately; never in a public issue, pull request or
discussion.

1. Open a private report: the repository's **Security** tab → **Report a vulnerability** (GitHub private
   vulnerability reporting). Say what is affected and how to reproduce it; only the maintainer,
   @ChristianPrzybulinski, sees it.
2. Keep tokens, passwords and personal data out of the report.
3. A credential that leaked (a token, a password, a key) is rotated first, before any other work; then report it.

You get an answer within 7 days. A fix is made on `main` and noted in `CHANGELOG.md` without exploit detail.

## Supported versions

Only the latest release, the version in `VERSION`, and `main` receive fixes.

## In scope

- the guard and format hooks (`plugins/guardrails/hooks/`) letting a destructive or secret-leaking command through;
- the install and sync tools (`platforms/tools/*.sh`) writing outside their destinations, following a symlink
  out of the target, or touching a file they do not own;
- a skill, rule or template that instructs an agent to expose secrets or to disable a safety check.
