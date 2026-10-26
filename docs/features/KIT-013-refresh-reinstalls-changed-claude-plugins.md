---
id: KIT-013
title: "refresh.sh reinstalls a Claude plugin whose content changed without a version bump"
status: done
confirmed: "2026-10-26 (owner, Stratics FEAT-101 activation coordination chat)"
issue: "#94"
pr: ""
---

# KIT-013 — refresh.sh reinstalls a Claude plugin whose content changed without a version bump

## Problem and evidence

[FACT] On 2026-10-26, after KIT-012 merged (#93, `7380b5b`), `platforms/tools/refresh.sh` printed
`refresh: 7380b5b 2026-10-26 main` and `platforms/tools/doctor.sh` reported every Claude line `ok`, yet
`~/.claude/plugins/cache/ai-kit/process-loop/11.0.0/skills/loop-orchestrate/SKILL.md` still lacked the KIT-012 text.
`claude plugin update process-loop@ai-kit --json` answered `"updateOutcome":"up_to_date"` with
`"message":"process-loop is already at the latest version (11.0.0)."`: Claude Code keys its plugin cache by the
manifest version, and `check_kit.py` pins every manifest to `VERSION`, which changes only at a release. The Codex
cache and the Devin lock picked the change up; only Claude stayed stale.

[FACT] `claude plugin uninstall process-loop@ai-kit --keep-data` followed by `claude plugin install
process-loop@ai-kit` replaced the cache with the new content and kept `enabledPlugins` in `~/.claude/settings.json`
unchanged (`process-loop@ai-kit: true`, `all@ai-kit: true`).

## Change

- `platforms/tools/refresh.sh`: after `claude plugin marketplace update ai-kit`, for each installed `<plugin>@ai-kit`,
  compare a content hash of the plugin directory in the marketplace clone with its `installPath` from
  `claude plugin list --json`; when they differ, run `claude plugin uninstall <plugin>@ai-kit --keep-data` and
  `claude plugin install <plugin>@ai-kit`, and print the plugins it reinstalled.
- `platforms/tools/doctor.sh`: a `warn` line per installed Claude plugin whose cache differs from the kit, naming
  `refresh.sh` as the fix.
- `platforms/tools/smoke.sh`: a stub `claude` that reports a stale cache, asserting the reinstall and that an
  up-to-date cache is left alone.

## Options considered

| Option | Verdict |
|---|---|
| A. Hash compare and reinstall in `refresh.sh`, warn in `doctor.sh` (chosen) | fixes every content-only merge; uses only public `claude plugin` commands; observed safe on 2026-10-26 |
| B. Bump `VERSION` (PATCH) on every content merge | release overhead per PR; one forgotten bump brings the stale cache back; release CI does not run today |
| C. Put the commit SHA in the manifest version | a commit cannot contain its own SHA; `check_kit.py` requires plain semver equal to `VERSION` |
| D. Delete `~/.claude/plugins/cache/ai-kit/` in `refresh.sh` | depends on Claude Code's private cache layout; loses the installed state |
| E. A `doctor.sh` warning only | detects the drift but leaves the fix to the owner by hand |

## Proof

`bash platforms/tools/check.sh`, `bash platforms/tools/smoke.sh` (with the new stale-cache case),
`python3 platforms/ci/validations/check_kit.py --links`; on the owner's machine, `refresh.sh` after a content-only
merge leaves the Claude cache equal to the kit.

## History

- 2026-10-26: confirmed (owner, chat).
