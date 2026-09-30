---
description: Secure development — CVEs, secrets, OWASP Top 10, authentication, authorization, personal data, auditing. Load when touching dependencies, auth, endpoints, sensitive-data persistence or CI.
trigger: model_decision
---

# Secure development

## Gates (fail the build/PR)

- **0 critical or high CVEs** in dependencies: OWASP Dependency-Check (Java) in CI, `failBuildOnCVSS=7`. False positive → suppression with justification and a review date.
- Secret detected in the diff (gitleaks/`gh secret scanning`) → PR blocked.
- New dependency only with a version published ≥7 days ago (supply chain).

## Secrets and credentials

- Source: environment variable or keychain. Never in code, yml, log, commit, chat.
- `.env.example` versioned with placeholders; `.env` in `.gitignore`.
- Secret leaked → rotate **this session**, then scan history (`gitleaks detect`) and siblings.

## Authentication and session

- Password → Argon2id (preferred) or bcrypt cost ≥ 12. Never plain MD5/SHA-1/SHA-256.
- Session token: random ≥128 bits, expires, revocable, never in URL/log.
- Access recovery: single-use, short-lived token, sent out of band.

## Authorization

- Per action **and** per entity: "may move *this* character", not "is logged in".
- Server is authoritative: client sends intent, server validates invariants and decides the result.
- Administrative tool: explicit role + audit of every use.

## Input and output

- Validate at the boundary (size, type, range, enum). Reject, don't "sanitize and carry on".
- Parameterized SQL only. No concatenation, no `nativeQuery` with a built-up string.
- Error to the client: code + generic message. Stack trace, SQL, internal path → log only.

## Personal data (LGPD)

- Collect the minimum. E-mail and IP are personal. Do not copy real legacy data into fixtures.
- Audit log: who, when, what, result. No password, token or sensitive payload.

## Condition → action

- New endpoint → checklist: auth? per-entity authz? validation? rate limit? audit log if it changes state?
- New dependency → local `mvn dependency-check:check` before the PR.
- New network message → size and rate limits defined in the contract.
