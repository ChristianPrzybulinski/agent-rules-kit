---
description: Current Git LFS quotas per GitHub plan (Free/Pro 10 GiB, Team 250 GiB). Load when configuring LFS or evaluating binary costs.
kind: fact
verified: "2026-09-29"
sources:
  - https://docs.github.com/en/billing/concepts/product-billing/git-lfs
---

# GitHub Git LFS — quotas


| Plan | Storage | Bandwidth/month |
|---|---|---|
| GitHub Free / Pro / Free for orgs | 10 GiB | 10 GiB |
| Team / Enterprise Cloud | 250 GiB | 250 GiB |

- Storage is metered by hourly usage; bandwidth resets every billing cycle.
- No payment method or $0 budget: exceeding quota **blocks** LFS until the next cycle (charges nothing).
- Open budget: metered billing per GiB (bandwidth) and per GiB-month (storage), no data packs since 2024/2025.
- Monitor: `git lfs ls-files -s` in the repo; account usage in Settings → Billing.
- Alternative for a large archive: keep binaries off GitHub (see `git-lfs-and-binaries.md`).
