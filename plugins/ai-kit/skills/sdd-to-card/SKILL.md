---
name: sdd-to-card
description: SDD step 9 — sync a FEAT to GitHub Issues/Projects. Use when opening, updating or closing its card. Not for PR operations (skill github-cli).
argument-hint: "FEAT-nnn [--project <number>]"
triggers:
  - user
disable-model-invocation: true
allowed-tools:
  - read
  - edit
  - exec
---

# SDD 9 — To Card

Process: `../sdd-constitution/references/sdd-process.md`. This step changes GitHub state; run it only on user invocation and never print a token.

## 1. Map the FEAT

- Issue title: `FEAT-nnn: <title>`.
- Body: link the FEAT and requirements; summarize problem/scope/criteria instead of copying the specification.
- Labels/Project status mirror FEAT status; non-null flag adds `flag`.
- `card` stores the issue number.

## 2. Create or update

If `card: null`, create the issue with `gh issue create`, write its number to frontmatter and commit that link. Otherwise use `gh issue edit` to update title/body/status labels.

Create missing `feature`/`status:*` labels when authorized. Add to a requested/configured Project and update its Status field; ask before creating a Project.

## 3. Close delivery

For `status: delivered`, close the issue with the delivered PR reference. Do not create separate cards for REQ/DEC/DEBT unless the user explicitly requests a debt issue.

## 4. Verify

Run `gh issue view <n>` and confirm title, status, links and FEAT `card` agree.

Done when: GitHub and FEAT identifiers/status/links match, the frontmatter change is committed, and no specification body was duplicated.
