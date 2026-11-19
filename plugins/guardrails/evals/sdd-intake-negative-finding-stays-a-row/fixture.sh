#!/usr/bin/env bash
# Scaffold for the eval case: a repository with a small docs/spec/ (one approved REQ, one FEAT whose row owns
# src/login.py, an empty needs/ folder) and a login that violates the REQ. A finding routes to a fix row (sdd-intake § 4).
set -euo pipefail
git init -q -b main .
git config user.email eval@example.invalid
git config user.name eval
mkdir -p docs/spec/needs docs/spec/requirements docs/spec/features src
printf 'project:\n  kind: business\n' > .ai-kit.yaml
printf -- '---\nproject: "shop"\nversion: "1.0.0"\nupdated: "2026-11-01"\n---\n\n# shop - Specification\n\n## Features\n\n| ID | Title | Status |\n|---|---|---|\n| FEAT-001 | Log in | in-progress |\n' > docs/spec/spec.md
printf -- '---\nid: REQ-F-001\nstatus: approved\nsource: NEED-001 S1\n---\n\n# REQ-F-001 - Refuse an empty password\n\nA login with an empty password is refused with the message "Password required".\n' > docs/spec/requirements/REQ-F-001.md
cat > docs/spec/features/FEAT-001.md <<'FEAT'
---
id: FEAT-001
title: "Log in"
status: in-progress
issue: "#7"
---

# FEAT-001 - Log in

## Tasks

| ID | Task | Files | Proof of completion | Covers | Depends on | Status |
|---|---|---|---|---|---|---|
| T1 | Add the login check: Plan § Design | `src/login.py`, `tests/test_login.py` | `python3 -m pytest tests/test_login.py` | CA-1 | — | done |

## History

- 2026-11-01 plan: created.
FEAT
printf 'def login(user, password):\n    return user == "admin" and password == "secret"\n' > src/login.py
git add docs src .ai-kit.yaml
git commit -q -m 'base'
