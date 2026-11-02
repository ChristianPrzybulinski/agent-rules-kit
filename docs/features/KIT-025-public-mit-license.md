---
id: KIT-025
title: "The kit is public under the MIT license"
status: done
confirmed: "2026-11-02 (owner, chat of the GitHub profile session: \"e o kit tambem\")"
issue: "#124"
pr: "#125"
---

# KIT-025 — The kit is public under the MIT license

## Problem and evidence

[FACT] The kit is a private repository with a proprietary `LICENSE` (#66, 2026-10-06): no copying, redistribution or
model training without written permission. A public repository under that text would be readable but not usable,
which contradicts a plugin marketplace. The owner chose MIT on 2026-11-02.

[FACT] Two vendored skills ship without their license text. `plugins/architect-core/skills/grilling/` (MIT,
mattpocock/skills) and `plugins/extras/skills/find-skills/` (MIT, vercel-labs/skills) hold only `SKILL.md` and
`VENDOR.md`; no file in the repository contains "Permission is hereby granted". MIT requires its notice in every copy.
Both upstream repositories keep the text in a root `LICENSE`, which `platforms/tools/vendor.sh` never fetched: its sparse
checkout took only the skill path.

[FACT] Publishing exposes every branch, pull request ref, tag, issue and release. On 2026-11-02, `gitleaks git` over
`--remotes=origin --remotes=pr --tags` scanned 247 commits: no leaks found. A pattern scan of every added line and of all
123 issues and pull requests, 16 comments and 26 releases found no real IP (only `127.0.0.1`, `0.0.0.0` and the version
`25.0.4.1`), no e-mail outside `example.invalid`/`example.test`/noreply, no password-manager, Proxmox or token reference,
and 4 `/Users/christian` paths in `docs/plans/2026-10-kit-assessment/assessment.md`. Commit metadata keeps 2 non-noreply
author e-mails; rewriting history was declined.

## Change

- `LICENSE`: the standard MIT text, copyright Christian Przybulinski, so GitHub detects the license; the third-party note
  moves to `README.md` § License.
- `platforms/tools/vendor.sh`: the sparse checkout also takes `/LICENSE`, `/LICENSE.md` and `/LICENSE.txt`; a skill
  folder without its own `LICENSE*` gets the upstream root's; install fails when neither exists, and `--check` fails on a
  skill without one. Re-vendoring adds only `grilling/LICENSE` and `find-skills/LICENSE`.
- `SECURITY.md`: reports go through GitHub private vulnerability reporting instead of a collaborators-only issue.
- `README.md`: the bootstrap clones over plain HTTPS without `gh auth`; new § License. `INDEX.md` and
  `docs/maintenance.md` § Third-party skills follow.
- Outside the tree, after the merge: repository visibility public and private vulnerability reporting enabled.

## Proof

`bash platforms/tools/vendor.sh --check` fails before the change (`FAIL: grilling missing a LICENSE file`,
`FAIL: find-skills missing a LICENSE file`) and passes after it (`vendor: lock consistent`);
`bash platforms/tools/check.sh`; `bash platforms/tools/smoke.sh`; `python3 platforms/ci/validations/check_kit.py --links`;
`gitleaks git --redact --log-opts="origin/main..HEAD"`.

## History

- 2026-11-02: confirmed (owner, chat) and done.
