---
id: KIT-NNN
title: "<what changes, as a sentence>"
status: confirmed
confirmed: "YYYY-MM-DD (owner, <where: chat of which session, issue, review>)"
issue: "#N"
pr: ""
---

# KIT-NNN — <title>

## Problem and evidence

[FACT] <what went wrong or what is missing, with the reproduction: repository, PR or issue, command and its output>

## Change

<the files that change and what each one gains; a rule line quoted exactly>

## Proof

<the kit gates: `bash platforms/tools/check.sh`, `bash platforms/tools/smoke.sh`,
`python3 platforms/ci/validations/check_kit.py --links`, plus any test the change adds>

## History

- YYYY-MM-DD: confirmed (<who>).
