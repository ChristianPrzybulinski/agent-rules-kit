---
description: Redis 7.4 for local dev and per-version licensing (≤7.2 BSD, 7.4–7.8 RSALv2/SSPLv1, ≥8.0 +AGPLv3). Load when proposing cache/session or pinning an image.
trigger: model_decision
verified: "2026-09-29"
sources:
  - https://redis.io/legal/licenses/
  - https://redis.io/blog/agplv3/
---

# Redis 7 — version and license

- Version chosen for local dev: **7.4** (latest 7.x minor on Docker Hub — tag `redis:7.4`). The 7.x line receives no new features; consider 8.x for new projects.

## License (important)

Source: https://redis.io/legal/licenses/ and https://redis.io/blog/agplv3/

| Version | License |
|---|---|
| ≤ 7.2 | BSD-3-Clause |
| 7.4 – 7.8 ("Community Edition") | dual: RSALv2 **or** SSPLv1 (neither OSI-approved) |
| ≥ 8.0 ("Redis Open Source", GA 2025-05-02) | triple: RSALv2 **or** SSPLv1 **or** AGPLv3 (OSI-approved) |

In short: Redis 7.4+ moved to RSALv2/SSPLv1 (Mar/2024); from 8.0 on, AGPLv3 returned as an option. For local/dev use this restricts nothing; relevant when distributing or offering Redis as a service.
