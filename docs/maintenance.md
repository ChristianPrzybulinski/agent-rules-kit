# Kit maintenance

## Versioning

`VERSION` (semver) + an entry in `CHANGELOG.md` + a `vX.Y.Z` tag. Pushing the tag triggers `.github/workflows/release.yml`, which validates tag == `VERSION` and creates the release with the changelog section — **releases are automatic**, do not create a release manually.

`LAYOUT_VERSION` (integer) bumps when the folder structure or an install destination changes — `refresh.sh` detects it and runs `install/all.sh --clean` (full reinstall). A content change without a layout change → `VERSION` only.

## Adding content

| Type | Steps |
|---|---|
| knowledge | copy `kit-knowledge.md` → `agents/knowledge/<domain>/` (frontmatter with `verified` + `sources`), list in `agents/knowledge/INDEX.md` |
| skill | copy `kit-skill.md` → `agents/skills/<type>/<name>/`, `name` = folder, list in the type's INDEX and in `agents/skills/INDEX.md`; normative detail that does not fit in 80 lines → `references/<topic>.md` (≤60, linked from SKILL.md) |
| template | `agents/templates/<prefix>-<name>.md` (regex `^(spec|doc|project|kit)-`), list in `agents/templates/INDEX.md` |
| index | `kit-index.md` (list only) or `kit-readme.md` (explains) — never both in the same folder |

## Third-party skills (vendor)

Policy: **never `npx skills add` directly into the agents**. Updating a vendored skill:

1. `git ls-remote https://github.com/<repo> HEAD` → new SHA.
2. Update the line in `platforms/kits/third-party/skills.lock` (name | repo | path | sha | license | date).
3. `platforms/install/third-party.sh` regenerates `agents/skills/vendor/<name>/` + `VENDOR.md`.
4. `platforms/tools/check.sh` (lock × VENDOR.md × schema) → commit.

Removing: delete the lock line + `git rm -r agents/skills/vendor/<name>`.

## What CI requires

`.github/workflows/ci.yml`: `check.sh` with `CI=1` (pyyaml/jsonschema mandatory — a local run without them runs in structural mode with a warning), `shellcheck` on `platforms/**/*.sh`, `check_kit.py --links`. `gitleaks.yml` on every push. Weekly Dependabot for actions.

This machine's prerequisites (2026-09-30): Godot 4.7.2 · JDK 25 (`/opt/homebrew/opt/openjdk@25`, keg-only — via `toolchains.xml`) and JDK 27 on PATH · Maven 3.9.16 · Node 26.10.0/npm 11.19.1 · Docker 29 + Compose v5 · gh 2.101 · git-lfs 3.8 · DBeaver · Krita. System Python 3 with `pyyaml` 6.0.3 / `jsonschema` 4.25.1 (`check.sh` runs in full mode locally; CI installs them anyway).
