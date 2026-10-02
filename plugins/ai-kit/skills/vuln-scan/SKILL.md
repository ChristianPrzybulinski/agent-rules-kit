---
name: vuln-scan
description: Scan for CVEs, secrets and changed endpoints. Use when preparing a sensitive PR, release or requested audit. Not for security design (skill secure-development).
argument-hint: "[deps | secrets | endpoints | all] (default: all)"
triggers:
  - user
agent: reviewer
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Vulnerability Scan

Gate: zero critical/high CVEs (CVSS at least 7), zero secrets, and evidence for authentication, authorization and validation on changed endpoints. Report findings; do not update dependencies or rewrite endpoints during the scan.

## 1. Select scope

Use the argument `deps`, `secrets`, `endpoints` or `all`. Record any skipped area as unverified.

## 2. Scan dependencies

For Java/Maven when `pom.xml` exists:

```bash
./mvnw -q org.owasp:dependency-check-maven:check -DfailBuildOnCVSS=7 -Dformats=JSON,HTML
```

Read `target/dependency-check-report.json`. For each CVE at or above 7, record dependency, version, CVE, CVSS, fixed version and transitive path. Use `versions:display-dependency-updates` and `dependency:tree -Dincludes=<groupId>` as evidence.

A false-positive suppression needs a reason and a review date within 90 days. For Docker, run `docker scout cves <image>` when available and reject `latest`; otherwise mark image scanning unverified. For Godot addons, record origin, version, license and last update; flag an untraceable addon.

## 3. Scan secrets

```bash
gitleaks detect --source . --redact -v
git log -p --all -S 'BEGIN PRIVATE KEY' --oneline | head
```

If gitleaks is unavailable, run a redacted `grep` for key, secret, password and token assignments while excluding `.git`, `target`, `.godot` and `node_modules`; label the result partial.

On a real finding, stop other work, report the type/file/commit without the value, and direct rotation plus a sibling scan in the current session.

## 4. Review changed endpoints

For every endpoint or network message in `git diff <base>...HEAD`, record evidence for authentication, per-entity authorization, input validation, size/rate limit, audit on state changes, and non-leaking errors. A cell without code or test evidence fails.

## 5. Report

```text
Scope: deps | secrets | endpoints | all
CVE gate: OK | FAILED — <critical/high counts>
| Dependency | Version | CVE | CVSS | Fixed in | Action |
Secrets: none | FOUND (<type, file, commit; no value>)
Endpoints: <evidence table>
Unverified: <missing tool or scope>
Next step: <smallest action that clears the gate>
```

Done when: every selected scope has literal tool output or is marked unverified, findings contain no secret values, and the verdict applies the CVSS 7 and zero-secret gates.
