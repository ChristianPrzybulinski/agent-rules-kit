# skills/quality/ — verification and quality

| Skill | Scope | When to use |
|---|---|---|
| `skeptic` | adversarial verification of a claim (against → for → verdict) | something "seems right" but was not proven |
| `validate-implementation` | confronts the delivery with the spec/request, runs gates, verdict READY/PARTIAL/NOT READY | before a PR or saying "done" |
| `vuln-scan` | CVEs in deps, secrets in the repo, OWASP checklist | PR touching dep/auth/network, release |
| `characterization-tests` | tests that pin the CURRENT behavior of legacy code | before refactoring/migrating/rebalancing |
| `secure-development` | CVEs, secrets, OWASP Top 10, auth, personal data, auditing | touching dependencies, auth, endpoints, CI |
