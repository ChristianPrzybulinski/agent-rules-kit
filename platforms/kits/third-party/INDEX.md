# third-party/ — pinned external skills

| File | Scope |
|---|---|
| `skills.lock` | one line per skill: `name \| repo \| path \| commit-sha \| license \| verified` |

`platforms/tools/vendor.sh` reads the lock and vendors into `plugins/ai-kit/skills/<name>/` (with `VENDOR.md`). Update: `git ls-remote` on the repo → new SHA in the lock → `vendor.sh` → `check.sh`. Never `npx skills add` into the kit.
