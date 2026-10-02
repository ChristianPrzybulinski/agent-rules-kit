---
name: secure-development
version: "1.1"
description: Security design for dependencies, auth, endpoints and sensitive data. Use when changing a trust boundary. Not for scanning changes (skill vuln-scan).
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Secure Development

## 1. Apply release gates

- Reject critical/high dependency CVEs: OWASP Dependency-Check uses `failBuildOnCVSS=7`.
- A suppression needs the false-positive reason and a review date.
- Accept a new dependency only after it has been published for at least seven days.
- Block a change containing a detected secret.

## 2. Handle secrets as an incident

- Read credentials only from environment variables or a keychain; version `.env.example` placeholders and ignore `.env`.
- Never place a password, token or key in source, YAML, logs, command output or chat.
- On exposure, stop the current work, warn first, rotate during this session, then run `gitleaks detect` on history and search sibling credentials.

## 3. Design authentication and sessions

- Hash passwords with Argon2id, or bcrypt cost at least 12; general-purpose hashes are invalid.
- Generate session tokens with at least 128 random bits; make them expiring, revocable and absent from URLs/logs.
- Recovery tokens are single-use, short-lived and sent out of band.

## 4. Enforce authorization and client distrust

- Authorize each action against the target entity, not only the authenticated role.
- Treat client messages as intent; the server validates every invariant and decides the result.
- Administrative actions require an explicit role and an audit event.

## 5. Protect boundaries and data

- Validate input size, type, range and enum at the boundary; reject invalid input.
- Use parameterized SQL; never concatenate a query or construct a `nativeQuery` string.
- Return stable error codes and generic messages; keep stack traces, SQL and internal paths out of client responses.
- Minimize personal data; e-mail and IP are personal. Fixtures never contain real personal data.
- Audit who, when, action and result without credentials or sensitive payloads.

## 6. Review each sensitive change

- Endpoint: authentication, entity authorization, validation, rate limit, non-leaking error, and audit for state changes.
- Dependency: run `mvn dependency-check:check` before the PR.
- Network message: define size and rate limits in the contract.
- Commit: inspect the diff for credentials, concatenated SQL, missing authorization and leaked internals.

Done when: the trust boundary has explicit validation and authorization, secrets are absent, and the CVE/password/token constants above are enforced or reported as blockers.
