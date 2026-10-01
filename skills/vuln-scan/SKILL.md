---
name: vuln-scan
version: "1.0"
description: Vulnerability scan — CVEs in dependencies (Java/Maven, Godot addons, Docker images), secrets in the repository and history, and an OWASP checklist on changed endpoints. Use before a PR touching dependencies/auth/network, on release, or periodically. Do not use for secure design guidance while writing code (skill secure-development).
argument-hint: "[deps | secrets | endpoints | all]  (default: all)"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Vuln Scan

Kit gate: **0 critical/high CVEs (CVSS ≥ 7)**, **0 secrets**, new endpoints with auth/authz/validation. Reports; does not fix automatically (updating a dependency can break — that is a normal task with tests).

## deps

Java/Maven (required if a `pom.xml` exists):
```bash
./mvnw -q org.owasp:dependency-check-maven:check -DfailBuildOnCVSS=7 -Dformats=JSON,HTML
```
Read `target/dependency-check-report.json`. For each CVE ≥7: dependency, version, CVE, CVSS, available fixed version (`./mvnw versions:display-dependency-updates`), transitive path (`./mvnw dependency:tree -Dincludes=<groupId>`).
Proven false positive → propose an entry in `dependency-check-suppressions.xml` with `<notes>` (reason + review date in 90 days). Never suppress without justification.

Docker (if a `Dockerfile`/`compose` exists): base images pinned by version tag (not `latest`); run `docker scout cves <image>` if available, otherwise record as unverified.

Godot: addons in `addons/` → origin, version, license and last update; an addon without a traceable source → flag.

## secrets

```bash
gitleaks detect --source . --redact -v      # if installed
git log -p --all -S 'BEGIN PRIVATE KEY' --oneline | head
```
Without gitleaks: `grep -rEn '(api[_-]?key|secret|password|token)\s*[:=]\s*["\x27][^"\x27]{8,}' --exclude-dir={.git,target,.godot,node_modules} .` and review manually; record that the scan was partial.
Real finding → **stop everything**, report first, direct rotation this session and a sibling scan. Never print the secret's value in the report.

## endpoints

For each endpoint/network message in the diff (`git diff <base>...HEAD`), table:

| Endpoint/Msg | Auth | Per-entity authz | Input validation | Size/rate limit | Audit (if it changes state) | Error doesn't leak internals |

A cell without evidence (code or test) = ✗.

## Verdict

```
Scope: deps | secrets | endpoints | all
CVE gate: OK | FAILED — N critical, M high
| Dependency | Version | CVE | CVSS | Fixed in | Action |
Secrets: none | FOUND (type, file, commit — no value)
Endpoints: table above
Unverified: <missing tool, uncovered scope>
Next step: <the smallest action that clears the gate>
```
