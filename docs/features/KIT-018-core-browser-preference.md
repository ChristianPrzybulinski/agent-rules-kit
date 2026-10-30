---
id: KIT-018
title: "The core rules carry the owner's browser preference"
status: done
confirmed: "2026-10-29 (owner, chat of the kit-validation session: \"Arrume os erros\")"
issue: "#107"
pr: ""
---

# KIT-018 — The core rules carry the owner's browser preference

## Problem and evidence

[FACT] The owner's browser preference was added by hand to the installed clone, at the end of
`~/.ai-kit/plugins/core/AGENTS.md`, the file that `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md` link to:

```text
## Browser preference

- Prefer Google Chrome for browser automation when its connection is available. Use the installed app at `/Applications/Google Chrome.app`, not a mounted installer. Honor explicit requests to open a page in the built-in Codex browser.
```

[FACT] After the 11.1.0 refresh on 2026-10-29, `platforms/tools/doctor.sh` exits 1 on that clone:

```text
FAIL: kit working tree is dirty
FAIL: AGENTS.md 64 lines exceeds 60
```

`platforms/tools/refresh.sh` refuses a dirty tree (`FAIL: refresh: working tree is dirty; refusing to update`), so the
11.1.0 refresh ran between a `git stash` and a `git stash pop` of that file. Every later refresh would need the same.

[FACT] The rule cannot move to a skill at no cost: the kit has no browser skill, and the skill description budget has
86 characters left (`doctor.sh`: `ok: skill descriptions 7114 chars (budget 7200)`). The browser is chosen at the first
browser tool call of a task, so the line stays always-on.

## Change

- `plugins/core/AGENTS.md` § Work loop gains one line:
  "Browser automation: prefer Google Chrome when its connection is available, using the installed
  `/Applications/Google Chrome.app`, never a mounted installer; an explicit request for the app's built-in browser
  (Codex or Claude) wins."
- § Communication's single line moves, unchanged, to the end of § Craft, and the `## Communication` heading goes, so
  `AGENTS.md` has 58 lines, within its 60-line limit (`check_kit.py`, `AGENTS_MAX_LINES`).

## Proof

`bash platforms/tools/check.sh`; `CI=1 bash platforms/tools/check.sh`; `bash platforms/tools/smoke.sh`;
`python3 platforms/ci/validations/check_kit.py --links`; `gitleaks git --redact --log-opts="origin/main..HEAD"`.

## History

- 2026-10-29: confirmed (owner, chat) and done.
