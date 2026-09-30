# third-party/ — pinned external skills

| File | Scope |
|---|---|
| `skills.lock` | one line per skill: `name \| repo \| path \| commit-sha \| license \| verified` |

`platforms/install/third-party.sh` reads the lock and vendors into `agents/skills/vendor/<name>/` (with `VENDOR.md`). Update: `git ls-remote` on the repo → new SHA in the lock → `third-party.sh` → `check.sh`. Never `npx skills add` into the agents.
