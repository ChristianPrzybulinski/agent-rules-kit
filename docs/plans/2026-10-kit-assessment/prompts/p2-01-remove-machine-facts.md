# P2-01 — Remove machine-specific facts from kit references and docs

Phase: 2 · Repos: kit · Branch to create: docs/p2-01-remove-machine-facts from main · Depends on: none · Effort: ~1.5 h

## Goal

Three `kind: fact` references and one kit doc state what is installed on the kit owner's laptop (Godot 4.7.2 binary, OpenJDK 25.0.4.1 under `/opt/homebrew`, Docker Compose v5.5.1, Claude Code 2.1.287, Node, gh, DBeaver, Krita). Replace every machine statement with the project-level pin that actually governs a build (`project.godot`, `AGENTS.md`, `.java-version`, `pom.xml`, the CI images) and keep only dated external facts with sources. Measurable result: `grep -rn -i 'this machine\|installed on\|keg-only\|Claude Code 2.1\|Devin Desktop with' plugins docs platforms/kits` returns 0 lines (5 today), `grep -rn '/opt/homebrew' plugins docs platforms` returns only the macOS launchd plist (3 today), and every gate stays green.

## Why

- assessment §4.2: `docs/maintenance.md`, `godot-4-versions.md` and `java-25-lts.md` carry "this machine" facts; for any other environment (Claude Code web, a GitHub runner, Devin Cloud, a new contributor) they are false statements stamped `[FACT]`.
- assessment §6 item A2: the kit must stop saying "installed on this machine"; fixed versions belong in the consuming repo's `AGENTS.md` (already true: `stratics-client/AGENTS.md:1` says `Godot 4.7.2`, `stratics-server/AGENTS.md:7` says `Java 25 LTS (maven.compiler.release=25)`) and in the Devin `environment.yaml` (P3-03).
- `plugins/dev-godot/skills/godot-standards/references/godot-4-versions.md:12` and `plugins/dev-java/skills/java-standards/references/java-25-lts.md:13` are the two lines a skill reads first when it "verifies" the toolchain; they report a laptop, not the project.
- `plugins/infra-core/skills/docker/references/compose-v2-vs-v5.md:13` records `v5.5.1` from `docker compose version` on the same laptop; the kit's own CI never runs that binary.
- `docs/maintenance.md:67` lists 13 desktop tools with versions dated 2026-10-01; `platforms/tools/doctor.sh` already produces that information on demand for the one machine where it is true.
- The kit's own rule already says the right thing: `plugins/dev-java/skills/java-standards/references/build-and-dependencies.md:11` ends with `Never "whatever is installed".`

## Current state

All paths are in the kit repo (v10.1.0).

```
plugins/dev-godot/skills/godot-standards/references/godot-4-versions.md:2:description: Godot 4.x versions (4.7.2 installed, matching CI image, TileMapLayer since 4.3, release policy). Load when configuring a Godot project or CI.
plugins/dev-godot/skills/godot-standards/references/godot-4-versions.md:12:- Version installed on this machine: **4.7.2.stable** (`godot --version` → `4.7.2.stable.official.ed1daf0bf`).
plugins/dev-godot/skills/godot-standards/references/godot-4-versions.md:13:- Matching CI image: `barichello/godot-ci:4.7.2` (tag exists on Docker Hub).
plugins/dev-java/skills/java-standards/references/java-25-lts.md:2:description: Java 25 LTS (GA 2025-09-16, Oracle support until 2030/2033, openjdk@25 keg-only installed, Maven toolchains). Load when configuring a Java project or pom.
plugins/dev-java/skills/java-standards/references/java-25-lts.md:13:- Installed on this machine: OpenJDK **25.0.4.1** via Homebrew (`brew install openjdk@25`, keg-only, `/opt/homebrew/opt/openjdk@25`).
plugins/infra-core/skills/docker/references/compose-v2-vs-v5.md:2:description: Docker Compose facts for the CLI plugin, obsolete version field and installed v5.5.1. Load when editing Compose files.
plugins/infra-core/skills/docker/references/compose-v2-vs-v5.md:13:- Version installed on this machine: **Docker Compose v5.5.1** (`docker compose version`).
plugins/infra-core/skills/docker/SKILL.md:17:Use `platforms/kits/docker/compose.yml`; read `references/compose-v2-vs-v5.md` for the installed Compose behavior and `../twelve-factor/SKILL.md` for application configuration.
docs/maintenance.md:67:This machine's prerequisites (2026-10-01): Godot 4.7.2 · JDK 25 (`/opt/homebrew/opt/openjdk@25`, keg-only — via `toolchains.xml`) and JDK 27 on PATH · Maven 3.9.16 · Node 26.10.0/npm 11.19.1 · Docker 29 + Compose v5 · gh 2.101 · git-lfs 3.8 · DBeaver · Krita · Devin Desktop with plugins from `main` · Codex desktop app (CLI not on PATH, so doctor uses app-only mode) · Claude Code 2.1.287. System Python 3 has `pyyaml` 6.0.3 and `jsonschema` 4.25.1.
platforms/kits/java-maven/toolchains.xml.example:13:      <jdkHome>/opt/homebrew/opt/openjdk@25/libexec/openjdk.jdk/Contents/Home</jdkHome>
```

Facts the new text points to (verified in the repos, do not re-derive from a local install):

```
platforms/kits/github/workflows/ci-godot.yml:9:  GODOT_IMAGE: barichello/godot-ci:4.7.2
platforms/kits/github/workflows/ci-java.yml:14:          distribution: temurin
platforms/kits/github/workflows/ci-java.yml:15:          java-version: '25'
platforms/kits/docker/README.md:20:`maven:3.9-eclipse-temurin-25` (build) → `eclipse-temurin:25-jre` (runtime). Both tags exist on Docker Hub (verified 2026-09-29). Adjust the `COPY` glob if the project produces more than one jar.
platforms/kits/java-maven/README.md:11:5. `toolchains.xml.example` → `~/.m2/toolchains.xml` (local, do not version). Needed because the PATH JDK may be ≠ 25 — the enforcer requires `[25,26)`.
```

Reference rules: `platforms/ci/schemas/reference.schema.json` (description at most 160 chars; `kind: fact` requires `verified` `YYYY-MM-DD` and `sources` with at least one `https://` URL); `platforms/ci/validations/check_kit.py:27` caps a reference at 60 lines and `check_kit.py:636` requires the owning `SKILL.md` to name the file. The references folders have no index file; the plugin `INDEX.md` tables list skills, not references, so no index changes are needed.

## Change

1. Edit `plugins/dev-godot/skills/godot-standards/references/godot-4-versions.md` (kit). Replace line 2 with:
   ```yaml
   description: Godot 4.x versions (project pin in project.godot and AGENTS.md, matching godot-ci image, TileMapLayer since 4.3). Load when configuring a Godot project or CI.
   ```
   Replace lines 12-13 with these two bullets (project pins instead of a binary on a laptop):
   ```markdown
   - The project pins its engine: `project.godot` `config/features` (for example `PackedStringArray("4.7", "Mobile")`) and the first line of the repo `AGENTS.md`. Never read the version from a local `godot --version`; a kit skill that needs the version reads those two files.
   - CI image: `barichello/godot-ci:<project version>`; the kit workflow `platforms/kits/github/workflows/ci-godot.yml` ships `4.7.2`. The tag must exist on Docker Hub for the pinned version: verify against https://hub.docker.com/r/barichello/godot-ci/tags before bumping it.
   ```
   Keep lines 14-16 unchanged. Keep `kind: fact`; keep `verified: "2026-09-29"` unless you re-open both URLs in `sources` during this task, in which case set `verified` to today's date.
2. Edit `plugins/dev-java/skills/java-standards/references/java-25-lts.md` (kit). Replace line 2 with:
   ```yaml
   description: Java 25 LTS (GA 2025-09-16, Oracle support to 2030/2033, pins in .java-version, pom.xml, toolchains, Temurin CI). Load when configuring a Java project or pom.
   ```
   Replace line 13 with:
   ```markdown
   - The project pins its JDK, not the machine: `.java-version` (`25`), `pom.xml` `<maven.compiler.release>25</maven.compiler.release>` and `~/.m2/toolchains.xml` copied from `platforms/kits/java-maven/toolchains.xml.example` (the enforcer requires `[25,26)`). CI: `actions/setup-java` with `distribution: temurin`, `java-version: '25'` (`platforms/kits/github/workflows/ci-java.yml`). Containers: `maven:3.9-eclipse-temurin-25` build, `eclipse-temurin:25-jre` runtime (`platforms/kits/docker/README.md`). Where the JDK lives on a developer's disk is `platforms/tools/doctor.sh` output, never a kit fact.
   ```
   Lines 1, 3-12 and 14-31 stay as they are. P2-12 owns any update of the Java/Spring facts themselves (JEP table, support dates); do not touch them here.
3. Edit `plugins/infra-core/skills/docker/references/compose-v2-vs-v5.md` (kit). Replace line 2 with:
   ```yaml
   description: Docker Compose facts for the CLI plugin form (docker compose), the obsolete version field and the v2+ requirement. Load when editing Compose files.
   ```
   Replace line 13 with:
   ```markdown
   - Requirement: Compose v2 or later as the `docker compose` CLI plugin; `docker compose version` must print `v2` or higher. The locally installed release is not recorded here; `platforms/tools/doctor.sh` reports it.
   ```
4. Edit `plugins/infra-core/skills/docker/SKILL.md:17` (kit): change `for the installed Compose behavior` to `for the Compose v2+ CLI behavior`. The line count (43) does not change.
5. Edit `docs/maintenance.md` (kit): delete line 67 and the blank line 66 that precedes it, so the file ends with the `## After merging to main` bullet list. Then append one bullet to that list, after line 65:
   ```markdown
   - Local tool versions (Godot, JDK, Maven, Docker, gh, Claude Code, Devin, Codex) are not documented in the kit; run `platforms/tools/doctor.sh` and read its output.
   ```
   `docs/INDEX.md` already lists `maintenance.md`; no index change.
6. Edit `platforms/kits/java-maven/toolchains.xml.example:13` (kit): replace the Homebrew path with a placeholder and give the two common layouts in an XML comment on the line above:
   ```xml
       <!-- Example paths: macOS Homebrew /opt/homebrew/opt/openjdk@25/libexec/openjdk.jdk/Contents/Home ; Linux /usr/lib/jvm/temurin-25-jdk -->
       <jdkHome>/path/to/jdk-25</jdkHome>
   ```
   Line 2 already says the file is local and not versioned; keep it. `platforms/kits/java-maven/README.md:11` needs no change.
7. Edit `CHANGELOG.md` (kit): add a bullet under `## [Unreleased]` / `### Changed` (line 10 today) using the proposed entry in Report back, with the before/after grep counts as proof.
8. Do not touch `VERSION`, any path, any plugin manifest, `platforms/kits/launchd/ai-kit.refresh.plist` (a macOS launchd file; `/opt/homebrew/bin` on its PATH is the platform convention, not a machine fact) or `platforms/tools/bootstrap.sh:2` ("Installs the plugin-first kit on this machine" describes the installer's job).

## Out of scope

- `docs/projects.md:3` and `docs/projects.md:23` say skills are "installed on the machine" and cite `platforms/install/` and `knowledge/`: the stale paths belong to P1-01, and the distribution model (per-repo `CLAUDE.md`, `.claude/settings.json`, `.claude/rules`, vendored skills) belongs to P2-04, P2-05 and P2-06. Do not edit that file.
- Absolute paths into the owner's home directory in stratics-docs (`docs/spec/ARCHITECT.md`, `ops/review-loop/config.json`, `.devin/config.json`, `ops/review-loop/prompts/*.md`, `docs/legacy/*.md`) and the Homebrew `jdkHome` in `stratics-server/toolchains.xml.example:13` are stratics project files. Mention them in Report back as a follow-up for P2-15 (and P3-03 for `environment.yaml`); do not edit the stratics repos.
- Java and Spring fact updates (JEP table, Boot 4.1.x): P2-12. JdbcClient, Flyway, ArchUnit: P2-13. Testcontainers and offline Maven: P2-14.
- Godot online references, gdtoolkit CI and the Godot boot proof: P3-01, P3-02, P1-06.
- The kit's own 10.x layout, paths and `VERSION`: frozen by P1-01.

## Acceptance criteria

- [ ] `grep -rn -i 'this machine\|installed on\|keg-only\|Claude Code 2.1\|Devin Desktop with' plugins docs platforms/kits` prints nothing (exit 1). Today it prints 5 lines.
- [ ] `grep -rn '/opt/homebrew' plugins docs platforms` prints exactly 2 lines: `platforms/kits/launchd/ai-kit.refresh.plist:23` and the XML comment in `platforms/kits/java-maven/toolchains.xml.example`. No reference or doc matches.
- [ ] `grep -c 'project.godot' plugins/dev-godot/skills/godot-standards/references/godot-4-versions.md` prints `1` or more; `grep -c '\.java-version' plugins/dev-java/skills/java-standards/references/java-25-lts.md` prints `1` or more; `grep -c 'v2 or later' plugins/infra-core/skills/docker/references/compose-v2-vs-v5.md` prints `1`.
- [ ] `tail -n 1 docs/maintenance.md` starts with `- ` (a bullet of the "After merging to main" list) and `grep -c "prerequisites" docs/maintenance.md` prints `0`.
- [ ] `wc -l plugins/dev-godot/skills/godot-standards/references/godot-4-versions.md plugins/dev-java/skills/java-standards/references/java-25-lts.md plugins/infra-core/skills/docker/references/compose-v2-vs-v5.md` shows each file at 60 lines or fewer (today 16, 31, 16).
- [ ] Each edited reference still has `kind: fact`, a `verified: "YYYY-MM-DD"` line and at least one `https://` source; the three `description:` values are each 160 characters or fewer (`awk 'NR==2{print length($0)-13}'` on each file prints a number of 160 or less).
- [ ] `platforms/tools/check.sh` exits 0.
- [ ] `platforms/tools/smoke.sh` exits 0.
- [ ] `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` reports `OK`.
- [ ] `python3 platforms/ci/validations/check_kit.py --links` exits 0 (reference schema, 60-line cap, SKILL.md linkage, backtick paths).
- [ ] `grep -n 'p2-01\|machine-specific' CHANGELOG.md` finds the new Unreleased bullet above the `## [10.1.0]` heading.
- [ ] `git diff --stat main` lists only: the three reference files, `plugins/infra-core/skills/docker/SKILL.md`, `docs/maintenance.md`, `platforms/kits/java-maven/toolchains.xml.example`, `CHANGELOG.md`.

## Conventions

- Everything committed is in English.
- No layout or path change: the 10.x layout is frozen; `plugins/`, `platforms/`, `docs/`, manifests and install destinations keep their paths.
- `VERSION` untouched (no release in this task).
- `CHANGELOG.md` gets a `## [Unreleased]` entry written with evidence (what, why, proof).
- References stay at 60 lines or fewer with frontmatter; `kind: fact` needs `verified` + `sources` (`platforms/ci/schemas/reference.schema.json`); description at most 160 chars; the owning `SKILL.md` must still name each reference file by name.
- `SKILL.md` at 80 lines or fewer (docker `SKILL.md` is 43 today); the skill `description:` lines are not touched, so the 7,200-char budget (6,803 today) does not move.
- `INDEX.md` or `README.md` of every touched folder lists every entry by name: no file is added or removed, so `docs/INDEX.md` and `platforms/kits/INDEX.md` stay as they are.
- Gates when the kit is touched: `platforms/tools/check.sh`; `platforms/tools/smoke.sh`; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`; `python3 platforms/ci/validations/check_kit.py --links`.
- Conventional Commits with Refs, for example `docs(references): replace machine-installed versions with project pins\n\nRefs: P2-01, assessment §4.2, §6 A2`.
- PR body = What / Why / How I tested (literal output of the four gates and the two acceptance greps) / Refs.
- Nothing here is Claude-specific; Devin or Claude Code can execute it with read, grep, edit and shell only.

## Report back

Final message format:

- done: list each edited path with the line numbers changed, then every command run (the four gates, the acceptance greps, `wc -l`) with its literal output.
- unverified: anything not reproduced (for example a Docker Hub tag or a `sources` URL you could not open; then `verified` was left at `2026-09-29` and say so).
- next step: the follow-ups outside this task: absolute home-directory paths in stratics-docs and the Homebrew `jdkHome` in `stratics-server/toolchains.xml.example` (P2-15, P3-03); per-repo distribution (P2-04, P2-05, P2-06); Java fact refresh (P2-12).
- Proposed CHANGELOG line (under `### Changed`):
  `- References and docs no longer describe the kit owner's machine: godot-4-versions.md, java-25-lts.md and compose-v2-vs-v5.md point to the project pins (project.godot, AGENTS.md, .java-version, pom.xml, toolchains, CI images) instead of "installed on this machine"; the machine prerequisites paragraph left docs/maintenance.md (doctor.sh reports local state); toolchains.xml.example uses a placeholder jdkHome. Evidence: grep for 'this machine|installed on|keg-only|Claude Code 2.1' over plugins, docs and platforms/kits went from 5 lines to 0 (P2-01, assessment §4.2 and §6 A2).`
