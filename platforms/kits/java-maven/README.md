# kit java-maven

Parent POM with the kit's quality gates on the Spring Boot 4.1.x BOM (3.5.x left OSS support on 2026-06-30). Versions verified on Maven Central on 2026-10-06; properties marked "verify" in the POM were not.

## How to use

1. In the project, copy `pom-parent.xml` to `server/pom.xml` (or the root), adjust `groupId`/`artifactId`/`version` and list the modules in `<modules>`.
2. Module structure: see `plugins/dev/skills/java-standards/references/build-and-dependencies.md` (`domain`, `application`, `adapter-*`, `bootstrap`). Modules declare the parent in `<parent>` and do **not** declare dependency versions.
3. Copy `.java-version` to the repo root.
4. `dependency-check-suppressions.xml` goes in the project root (the parent references it by name).
5. `toolchains.xml.example` → `~/.m2/toolchains.xml` (local, do not version). Needed because the PATH JDK may be ≠ 25 — the enforcer requires `[25,26)`.
6. Wrapper: generate in the project with `mvn wrapper:wrapper -Dmaven=3.9.16` (binaries are **not** distributed in this kit).

## Gates

- **Always**: `spotless:check` (google-java-format), JaCoCo report, enforcer (Java `[25,26)`, Maven `[3.9,)`, no duplicate dependencies in the POM).
- **`domain-gate`** (automatic): a module with the `src/main/java/.domain` marker (empty file) gets JaCoCo `check` 100% line+branch and PITest `mutationCoverage` (threshold 80, JUnit 5). Chosen for being declarative — alternative: declare both plugins in the domain module's `pom.xml`.
- **`fast`**: `-Pfast` skips PITest and dependency-check. Tests are **not** skipped (`skipTests` is untouched).
- **`release`**: `-Prelease` adds `requireReleaseDeps` (no SNAPSHOT).
- **Tomcat override**: Boot 4.1.1 manages Tomcat 11.0.24, which fails dependency-check; see the comment above `<dependencyManagement>` in the parent POM.

## CI

`platforms/kits/github/workflows/ci-java.yml` runs `spotless:check verify` + dependency-check in a separate job.
