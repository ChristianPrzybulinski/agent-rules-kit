# Load test — [scenario] — YYYY-MM-DD

FEAT/REQ: `REQ-NF-xxx`  ·  Server: `[repo @ commit]`  ·  Tool: `[synthetic clients: cmd/script @ commit]`

## Hypothesis

[HYPOTHESIS] [e.g.: 200 simultaneous sessions in 1 region keep p95 response to `Move` < 100 ms]

## Environment

| Item | Value |
|---|---|
| Hardware/VM | [CPU, RAM] |
| JVM | [version, `-Xmx`, GC] |
| Database | [version, pool size] |
| Network | [local | LAN | injected latency N ms] |

## Scenario

- Profile: [N clients, ramp X/s, duration Y min, message mix %]
- Seed/fixtures: [`...`] (reproducible)

## Metrics

| Metric | Target | Measured | Source |
|---|---|---|---|
| p50/p95/p99 [msg] | | | [Micrometer/log] |
| errors/s | 0 | | |
| CPU / heap / GC pause | | | |
| DB connections / lock wait | | | |
| event queue (max size) | | | |

## Result

- Verdict: [FACT] hypothesis confirmed / refuted at [breaking point]
- Observed bottleneck: [`file/component`] — evidence: [...]

## Unverified / limitations

- [e.g.: real network, real clients, invented message mix]
