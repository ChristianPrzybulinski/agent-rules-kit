---
id: KIT-024
title: "The review-loop kit says the loop tool moves to its own repository on a trigger, never into the kit"
status: done
confirmed: "2026-11-01 (owner, approval of Stratics DPRO-011 amendment 2026-11-01d, dev-game-studio/stratics#3258)"
issue: "#122"
pr: "#123"
---

# KIT-024 — The review-loop kit says the loop tool moves to its own repository on a trigger, never into the kit

## Problem and evidence

[FACT] `platforms/kits/review-loop/README.md:21` (§ Decision on the loop tool, `origin/main` `b987444`) said the loop tool stays in the project at `ops/review-loop/loop.py` and "moves under `platforms/tools/`" once its hard-coded project literals read from config.

[FACT] Stratics DPRO-011 amendment 2026-11-01d, approved by the owner on 2026-11-01 ("Aprovo, merge") and merged as dev-game-studio/stratics#3258 (`89177f9`), rejected the kit as the loop's home. The loop stays in the monorepo at `platform/review-loop/` and splits into a project-neutral engine and a Stratics profile, with a boundary test. The engine moves to its own repository when a trigger holds: (a) a second project is going to run the loop, (b) a second OS needs its own release of the engine, or (c) someone needs the engine without the game. A trigger is enough only when the boundary test is green with no Stratics entry left in the engine's allowlist. Its item 7 asks for this KIT change, written by hand under the amendment 2026-10-07 ("The kit stays outside").

[FACT] Three more live lines cite the path the project left: `plugins/process-loop/skills/loop-orchestrate/SKILL.md:22` (§ 0 reads the project's `ops/review-loop/README.md`) and `platforms/kits/review-loop/config.example.json:57,151` (`full_risk_paths` and `owner_merge_paths` hold `ops/review-loop/**`). The Stratics `platform/review-loop/config.json` on `main` holds `platform/review-loop/**` in both lists, and `platform/review-loop/README.md` exists there.

## Change

- `platforms/kits/review-loop/README.md` § Decision on the loop tool: the tool stays in the project (Stratics: `platform/review-loop/`, DPRO-011 2026-11-01d) and splits into a neutral engine and a project profile behind a boundary test. It moves to its own repository when one of the three triggers holds and the boundary test is green with no project entry left; it never moves into the kit. The integration repository list joins the hard-coded literals, as the amendment's item 2 lists it.
- `plugins/process-loop/skills/loop-orchestrate/SKILL.md` § 0: the project's `platform/review-loop/README.md`.
- `platforms/kits/review-loop/config.example.json`: `platform/review-loop/**` in `full_risk_paths` and `owner_merge_paths`.
- Not changed: the dated `ops/review-loop` citations in `CHANGELOG.md` and `docs/plans/2026-10-kit-assessment/`, which record the layout of their day.

## Proof

- `bash platforms/tools/check.sh`
- `bash platforms/tools/smoke.sh`
- `python3 platforms/ci/validations/check_kit.py --links`
- `grep -rn 'ops/review-loop' platforms plugins` prints nothing.

## History

- 2026-11-01: confirmed (owner, approval of DPRO-011 amendment 2026-11-01d in dev-game-studio/stratics#3258).
- 2026-11-01: gates green at host load 17–27 (`check_kit.py --links`, `check.sh`, `CI=1 check.sh`, `smoke.sh`, `gitleaks`); PR #123 opened, not merged.
