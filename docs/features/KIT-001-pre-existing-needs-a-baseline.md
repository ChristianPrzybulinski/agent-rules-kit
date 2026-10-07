---
id: KIT-001
title: "A failure is pre-existing only against a baseline before your first change"
status: done
confirmed: "2026-10-07 (owner, chat of the Stratics architect session that ran the night batches)"
issue: "#69"
pr: "#68"
---

# KIT-001 — A failure is pre-existing only against a baseline before your first change

## Problem and evidence

[FACT] On 2026-10-07 a Stratics architect session ran a series of eight restructure PRs (DPRO-015). A red `dat-importer`
test was called pre-existing because it also failed on `main`, but that `main` already held the session's own earlier
PRs of the series: P2, P5 and P6 had edited `docs/legacy/sample-manifest.md`, whose sha256 seven pilot provenance rows
pin. The regression shipped and needed a fix PR (ChristianPrzybulinski/stratics-docs#580). It was the night run's
improvement 23; the project holds the same rule as `docs/guide/ARCHITECT.md` delta 10 (stratics-docs#590).

## Change

`plugins/core/AGENTS.md` § Truth gains one line:

> A failure is "pre-existing" only after the same command failed, this session, on the commit before your first change
> (for a PR: its base). A mid-series `main` is no baseline.

## Proof

`bash platforms/tools/check.sh` → `check: OK (14 plugins, 46 skills, 3 rules, 22 templates, 22 indexes, 89 links, 12 hook
cases)`; `bash platforms/tools/smoke.sh` → `smoke: OK`; CI `check` and `scan` green on #68.

## History

- 2026-10-07: confirmed (owner, chat) and implemented by hand in #68 (merged `4ba811d`), before `docs/features/` existed;
  recorded here and in issue #69 the same day.
