# P2-14 — Testcontainers, offline Maven and fast profile guidance

Phase: 2 · Repos: kit (agent-rules-kit), stratics-server · Branch to create: docs/p2-14-testcontainers-offline-fast from main (same name in both repos, one PR each) · Depends on: P2-12 · Effort: ~3 h

## Goal

Make the Java skill tell a sandboxed agent how to build without network (`dependency:go-offline` once in the snapshot, then `./mvnw -o`), what `-Pfast` skips and what it never skips, the "lint and tests at most 5 min each" budget, and the Testcontainers pattern Spring Boot recommends (`@ServiceConnection` on a container declared as a `@Bean` in a `@TestConfiguration`, local `reuse`), then put the resulting commands into stratics-server `AGENTS.md`. Measurable result: the kit reference `build-and-dependencies.md` gains a "Sandboxed agents" section and stays at 60 lines or fewer; a new `kind: fact` reference `testcontainers.md` (60 lines or fewer, linked from `SKILL.md`) exists; stratics-server `AGENTS.md` § Commands lists the offline and `-Pfast` lines and § Patterns has one Testcontainers bullet; `./mvnw -o -q spotless:check verify` passes on a cache filled by the documented snapshot command; all four kit gates stay green.

## Why

- assessment §6 G3: Testcontainers with `@ServiceConnection` and containers as beans (the Boot docs warn that a static `@Container` fights the `ApplicationContext` cache), `reuse` and `-Pfast` documented in the server `AGENTS.md` to keep "tests at most 5 min"; `./mvnw -o verify` after `dependency:go-offline` in the environment snapshot for sandboxed agents without network.
- assessment §5.1, Spring row: verdict "right; the offline mode and the `@ServiceConnection` pattern are missing from the kit" (the server already has ArchUnit and Testcontainers).
- The kit names `-Pfast` once, `plugins/dev-java/skills/java-standards/references/build-and-dependencies.md:46`, and `platforms/kits/java-maven/README.md:18` defines it ("Tests are **not** skipped"); nothing in the kit says `go-offline`, `-o`, `@ServiceConnection` or `reuse` (`grep -rn "go-offline\|ServiceConnection\|testcontainers.reuse" plugins platforms` prints nothing).
- stratics-server has no `fast` profile: `grep -c "<profiles>" pom.xml` prints `0`, while `pom.xml:262-268` binds PITest `mutationCoverage` to `verify`, so every local `verify` pays mutation testing (598 tests at the import baseline, stratics-server `README.md:13`).
- stratics-server mixes two container styles with no rule: `src/test/java/br/com/pos/adapters/outbound/persistence/JdbcRepositoriesIT.java:31` and `CommandTransactionIT.java:35` use static `@Container` (plain JUnit, fine), while the five `@SpringBootTest` classes (`WebSocketHandshakeIT`, `GameProtocolIT`, `abuse/*`) boot on the JDBC-URL driver, `src/test/resources/application.properties:2`. A future `@SpringBootTest` copying the static `@Container` style would hit the Boot warning.

## Current state

All kit paths are in agent-rules-kit (v10.1.0, after P2-12). `wc -l`: `build-and-dependencies.md` 47, `SKILL.md` 53, stratics-server `AGENTS.md` 69, `pom.xml` 298.

```text
plugins/dev-java/skills/java-standards/references/build-and-dependencies.md:1:---
plugins/dev-java/skills/java-standards/references/build-and-dependencies.md:3:kind: detail
plugins/dev-java/skills/java-standards/references/build-and-dependencies.md:42:## Condition → action
plugins/dev-java/skills/java-standards/references/build-and-dependencies.md:46:- Slow build → `mvn -T 1C` and profiles: `-Pfast` skips PITest/Dependency-Check locally; CI runs everything.
plugins/dev-java/skills/java-standards/references/build-and-dependencies.md:47:- Release → `mvn -B release:prepare release:perform` or version via CI from the commits; never hand-edit the version on release day.
plugins/dev-java/skills/java-standards/SKILL.md:19:Read `references/build-and-dependencies.md` for Maven/module gates and `references/java-25-lts.md` for verified Java 25 and Spring Boot 4.1 facts.
plugins/dev-java/skills/java-standards/references/testcontainers.md (new file; no index lists references: plugins/dev-java/INDEX.md:7 lists the skill only, and check_kit.py:637 requires SKILL.md to name the file)
platforms/kits/java-maven/pom-parent.xml:212-218: <profile><id>fast</id> sets <pitest.skip>true</pitest.skip> and <dependency-check.skip>true</dependency-check.skip>; :85 and :101 wire them into <skip>.
stratics-server/AGENTS.md:28:## Commands
stratics-server/AGENTS.md:34:./mvnw verify                             # unit + integration (Testcontainers)
stratics-server/AGENTS.md:36:./mvnw spotless:check verify              # gate before commit/PR
stratics-server/AGENTS.md:50:- New domain test → no `@SpringBootTest`; pure JUnit. `@SpringBootTest` only for real integration.
stratics-server/AGENTS.md:63:- Ask first: change `pom.xml`; edit an already-applied migration; change Spring auto-config; change a public protocol contract.
stratics-server/pom.xml:296:    </build>
stratics-server/pom.xml:298:</project>
stratics-server/.github/PULL_REQUEST_TEMPLATE.md:32:- [ ] No direct `CHANGELOG.md` edit (DPRO-011)
stratics-docs/.github/workflows/reusable-ci-java.yml:70:        run: ./mvnw -B -ntp spotless:check verify
stratics-docs/.github/workflows/reusable-ci-java.yml:108:        run: ./mvnw -B -ntp org.owasp:dependency-check-maven:13.0.0:check -DfailBuildOnCVSS=7 -DnvdApiKeyEnvironmentVariable=NVD_API_KEY
```

Facts to verify before writing (network was unavailable when this prompt was written): (a) the static `@Container` warning and the `@ServiceConnection` + `@TestConfiguration(proxyBeanMethods = false)` pattern, verify against the Spring Boot 4.1 reference, Testing > Testcontainers, before relying on it; (b) the artifact that provides `@ServiceConnection` in Boot 4.1 (`spring-boot-testcontainers` or a starter), verify against the same page; (c) `testcontainers.reuse.enable=true` in `~/.testcontainers.properties` plus `.withReuse(true)`, verify against java.testcontainers.org, Features > Reuse; (d) the "lint at most 5 min, tests at most 5 min" budget, verify against docs.devin.ai, repository setup page, and quote it as "Devin repo-setup guidance" only if the page still says so.

## Change

1. Edit `plugins/dev-java/skills/java-standards/references/build-and-dependencies.md` (kit). Insert before line 42 (`## Condition → action`) this section verbatim; the file then has 55 lines or fewer. Do not change line 46; its `-Pfast` semantics are the ones repeated here.

```markdown
## Sandboxed agents (no network at build time)

- Snapshot or maintenance step, online, once: `./mvnw -q dependency:go-offline && ./mvnw -q -Pfast spotless:check verify`. The second command caches what `go-offline` misses (Spotless formatter, Surefire/Failsafe providers, PITest JUnit 5 plugin) and pulls the Testcontainers images; `-o` covers Maven artifacts only, never Docker images.
- Task step, offline: `./mvnw -o -q spotless:check verify`. Add `-Pfast` when the budget is tight: it skips PITest and Dependency-Check and never skips tests; CI runs everything.
- Budget: lint and tests at most 5 minutes each (Devin repo-setup guidance). Over budget locally: `-Pfast` plus `-Dtest=<Class>`; never `-DskipTests` in a gate.
- Integration tests on real services: read `testcontainers.md` in this folder.
```

2. Create `plugins/dev-java/skills/java-standards/references/testcontainers.md` (kit, new file, 60 lines or fewer). Frontmatter: `description` (at most 160 chars, e.g. "Testcontainers in Spring Boot and plain JUnit: @ServiceConnection beans, when static @Container is safe, local reuse, sandbox caching."), `kind: fact`, `verified: <today, YYYY-MM-DD>`, `sources:` with the Spring Boot Testcontainers page and the Testcontainers reuse page (https URLs, verified per the facts list above). Body outline, in this order: (1) Spring context tests: one `@TestConfiguration(proxyBeanMethods = false)` class with a `@Bean @ServiceConnection PostgreSQLContainer<?>` (one fenced Java block of at most 12 lines), imported with `@Import` or applied through `@SpringBootTest` on the test slice; why: a static `@Container` is started and stopped per test class while the `ApplicationContext` is cached across classes, so the cached `DataSource` points at a stopped container; the JDBC-URL shortcut (`jdbc:tc:postgresql:<ver>:///db`) is the acceptable alternative when no bean is needed. (2) Plain JUnit tests without Spring: `@Testcontainers` + static `@Container` is correct; keep the container per class and truncate between tests. (3) Local reuse: `testcontainers.reuse.enable=true` in `~/.testcontainers.properties` plus `.withReuse(true)` on the container; the kit's sync never writes that file; CI never reuses. (4) Sandbox: the image must already be in the Docker cache (the snapshot's test run pulls it); `-o` does not help Docker. (5) Pin the image tag (`postgres:18`), never `latest`. No project identifier (`br.com.pos`, `DTEC-`, `REQ-`, `FEAT-`) in the file.

3. Edit `plugins/dev-java/skills/java-standards/SKILL.md` (kit). Insert after line 19 the line `Integration tests on a real database or broker: read `references/testcontainers.md` (Spring Boot container beans, reuse, sandbox caching).` If P2-13 is already merged and line 19 became a list of references, append `testcontainers.md` to that list instead. The `description:` line does not change; the file stays at 80 lines or fewer.

4. Edit `CHANGELOG.md` (kit) under `## [Unreleased]`, `### Added`, one bullet (proposed text in Report back).

5. stratics-server, separate PR. Check first: `grep -c "<profiles>" pom.xml` prints `0` today, so `-Pfast` is missing. `AGENTS.md:63` lists `pom.xml` under "Ask first": put the `pom.xml` change in its own commit, name it in the PR "What" section, and if the executor can reach the owner, ask before pushing; otherwise open the PR as a draft and say the pom commit awaits approval. Insert before `pom.xml:296` (`</build>`), after it (i.e. between `</build>` and `</project>`), this block verbatim. Dependency-Check has no bound execution in this pom (CI calls the goal explicitly, `reusable-ci-java.yml:108`), so the profile skips PITest only; tests still run:

```xml
    <profiles>
        <!-- Local fast gate: skips PITest only (CI runs it, reusable-ci-java.yml). Tests are never skipped. -->
        <profile>
            <id>fast</id>
            <build>
                <plugins>
                    <plugin>
                        <groupId>org.pitest</groupId>
                        <artifactId>pitest-maven</artifactId>
                        <configuration>
                            <skip>true</skip>
                        </configuration>
                    </plugin>
                </plugins>
            </build>
        </profile>
    </profiles>
```

6. Edit stratics-server `AGENTS.md`. In § Commands, after line 36 (`./mvnw spotless:check verify              # gate before commit/PR`) add these three lines inside the same fenced block:

```bash
./mvnw -q dependency:go-offline && ./mvnw -q -Pfast spotless:check verify   # snapshot only, online: fills ~/.m2 and the Docker image cache
./mvnw -o -q spotless:check verify        # same gate without network (sandboxed agent)
./mvnw -Pfast verify                      # skips PITest only; tests still run; CI runs everything
```

In § Patterns, after line 50 (`- New domain test → ...`), add one bullet: `- Integration test needing PostgreSQL → `@SpringBootTest` classes boot on the `jdbc:tc:postgresql:18:///stratics` URL (`src/test/resources/application.properties`); a plain JUnit IT uses `@Testcontainers` + static `@Container` (as `JdbcRepositoriesIT`); never a static `@Container` inside a `@SpringBootTest` class, declare it as a `@Bean @ServiceConnection` in a `@TestConfiguration`. Local runs: `testcontainers.reuse.enable=true` in `~/.testcontainers.properties`.` Do not edit `CHANGELOG.md` in stratics-server (`PULL_REQUEST_TEMPLATE.md:32`, DPRO-011).

7. Prove the offline path in stratics-server before opening the PR: `mv ~/.m2/repository ~/.m2/repository.bak` (restore afterwards), run the snapshot command from step 6 online, then `./mvnw -o -q spotless:check verify`. If the offline run fails with "Cannot access central in offline mode" for an artifact, add a `./mvnw -q dependency:get -Dartifact=<g:a:v>` line to the snapshot comment in `AGENTS.md` for that artifact and say so in the PR. Record wall-clock time of `./mvnw -Pfast verify` and of `./mvnw verify` with `time`; paste both in "How I tested".

## Out of scope

- P2-12: Java 25 / Boot 4.1 facts, `build-and-dependencies.md:13` and `:24`, `SKILL.md:19` and `:43`, the template; this task starts after it is merged and keeps its lines.
- P2-13: `references/jdbcclient-flyway.md`, `references/archunit-rules.md` and their `SKILL.md` links; do not add JdbcClient or ArchUnit content to `testcontainers.md`.
- P2-01: removing machine-specific facts; do not add any `/opt/homebrew`, `~/.m2` absolute machine path or local JDK version to the kit (the `~/.m2` and `~/.testcontainers.properties` home-relative names are allowed).
- P3-03: `environment.yaml` for Devin and the playbooks; this task documents the snapshot command, P3-03 puts it in the Devin environment file.
- P2-15: applying generated agent configuration to the Stratics repos; this task edits only `AGENTS.md` and `pom.xml` in stratics-server.
- `platforms/kits/java-maven/pom-parent.xml` and its `README.md`: the kit's own `fast` profile already matches; no change.
- The existing static `@Container` fields in `JdbcRepositoriesIT` and `CommandTransactionIT` (plain JUnit, correct as they are) and the five `@SpringBootTest` classes: no test code changes.

## Acceptance criteria

Kit:
- [ ] `grep -c "Sandboxed agents" plugins/dev-java/skills/java-standards/references/build-and-dependencies.md` prints `1`; `grep -c "dependency:go-offline" ...` prints `1`; `grep -c "never skips tests" ...` prints `1`; `wc -l` prints 60 or fewer; line 3 is still `kind: detail`.
- [ ] `test -f plugins/dev-java/skills/java-standards/references/testcontainers.md`; `wc -l` prints 60 or fewer; `grep -c "^kind: fact" ...` prints `1`; `grep -c "^verified: 2026-" ...` prints `1`; `grep -c "https://" ...` prints 2 or more; `grep -c "ServiceConnection" ...` prints 2 or more; `grep -c "testcontainers.reuse.enable=true" ...` prints `1`; `grep -cE "br\.com\.pos|DTEC-|REQ-|FEAT-" ...` prints `0`.
- [ ] `grep -c "testcontainers.md" plugins/dev-java/skills/java-standards/SKILL.md` prints `1`; `wc -l` prints 80 or fewer; `git diff main -- plugins/dev-java/INDEX.md` is empty; `git diff main -- VERSION` is empty.
- [ ] `grep -c "P2-14" CHANGELOG.md` prints `1` under `## [Unreleased]`.
- [ ] `platforms/tools/check.sh` exits 0; `platforms/tools/smoke.sh` exits 0; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` prints `OK`; `python3 platforms/ci/validations/check_kit.py --links` exits 0.

stratics-server:
- [ ] `grep -c "<id>fast</id>" pom.xml` prints `1`; `grep -c "<profiles>" pom.xml` prints `1`; `grep -c "skipTests" pom.xml` prints `0`.
- [ ] `grep -c "dependency:go-offline" AGENTS.md` prints `1`; `grep -c "./mvnw -o -q spotless:check verify" AGENTS.md` prints `1`; `grep -c "./mvnw -Pfast verify" AGENTS.md` prints `1`; `grep -c "ServiceConnection" AGENTS.md` prints `1`; `git diff main -- CHANGELOG.md` is empty.
- [ ] `./mvnw -o -q spotless:check verify` exits 0 after the snapshot command on an emptied `~/.m2/repository` (step 7); `./mvnw -Pfast verify` exits 0 and its output contains no `PIT >>` lines (`./mvnw -Pfast verify | grep -c "PIT >>"` prints `0`), while `./mvnw verify | grep -c "PIT >>"` prints 1 or more.
- [ ] `./mvnw spotless:check verify` exits 0 (the gate), pasted literally in the PR.
- [ ] PR body follows `.github/PULL_REQUEST_TEMPLATE.md`: What / Why / How I tested / Proof block with lines `grep -c "<id>fast</id>" pom.xml`, `grep -c "dependency:go-offline" AGENTS.md`, `./mvnw -Pfast -q verify` (all first words are in the stratics-docs `ops/review-loop/config.json` `proof_allowlist`) / Checklist; `Refs:` the kit PR; the `pom.xml` change is a separate commit named in "What".

## Conventions

- Everything committed is in English; plain ASCII punctuation in new text.
- No layout or path change (10.x layout frozen): the new reference lives in `plugins/dev-java/skills/java-standards/references/`, nothing moves.
- `VERSION` untouched; `CHANGELOG.md` (kit) gets a `## [Unreleased]` entry with what, why and proof.
- INDEX.md rule: `plugins/dev-java/INDEX.md` lists skills, rules and templates by name, not references, so it does not change; `check_kit.py:637` is the index for references (`SKILL.md` must name the file).
- References: 60 lines or fewer with frontmatter; `kind: fact` needs `verified` (YYYY-MM-DD) and `sources` (https URLs); `kind: detail` does not (`platforms/ci/schemas/reference.schema.json`). `SKILL.md` 80 lines or fewer; the skill `description` is not edited (budget 6,803 of 7,200 chars stays).
- `check_kit.py:832` resolves backtick paths ending in `.md` inside skills: write `testcontainers.md` in backticks only once the file exists in the same commit.
- Conventional Commits with `Refs:`; kit commit `docs(dev-java): sandboxed Maven, -Pfast and Testcontainers guidance (P2-14)`; server commits `docs(agents): offline and fast gate lines, Testcontainers rule (P2-14)` and `build(pom): add fast profile that skips PITest only (P2-14)`.
- PR body = What / Why / How I tested (literal output) / Refs; the server PR additionally follows its template (Proof block, Checklist, no `CHANGELOG.md` edit).
- Kit gates: `platforms/tools/check.sh`; `platforms/tools/smoke.sh`; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"`; `python3 platforms/ci/validations/check_kit.py --links`. stratics-server gate: `./mvnw spotless:check verify`.
- Executor may be Devin or Claude Code; nothing here is Claude-specific.

## Report back

Final message, in this order:
1. done: each file created or edited with repo prefix (`kit:` / `server:`), and every command from Acceptance criteria with its literal output (exit code, grep count, `wc -l`, the two `time` results from step 7).
2. unverified: each of the four facts (a)-(d) that could not be checked against its source, and whether the offline run needed an extra `dependency:get`.
3. next step: the PR URLs, whether the server PR is a draft awaiting the `pom.xml` approval, and the prompt that should run next (P3-03 consumes the snapshot command).
4. Proposed CHANGELOG line (kit, `### Added`): `- `java-standards`: "Sandboxed agents" section in `references/build-and-dependencies.md` (go-offline snapshot, `./mvnw -o` task runs, `-Pfast` never skips tests, 5-minute budget) and new `references/testcontainers.md` (`@ServiceConnection` container beans, static `@Container` only outside Spring, local reuse, image caching). Evidence: the kit named `-Pfast` once and nothing about offline builds or `@ServiceConnection`; stratics-server had no `fast` profile and PITest bound to `verify` (P2-14, assessment §6 G3).`
