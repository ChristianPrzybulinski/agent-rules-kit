# [MessageName] — [command | event | response | error]

Direction: [C→S | S→C | both]  ·  Since `protocol_version`: [x.y]  ·  FEAT: `FEAT-xxx`

## Purpose

[One sentence: what the sender wants to happen / what the receiver needs to know.]

## Fields

| Field | Type | Req. | Limits | Validated by | Notes |
|---|---|---|---|---|---|
| `[field]` | [string/int/uuid/enum] | yes/no | [size, range, regex] | server / client (UX) | |

Common envelope (id, correlation, sequence, timestamp): see `protocol/README.md`.

## Semantics

- Idempotency: [dedupe key | not applicable (read-only)]
- Ordering: [per session | per entity `[x]`]; out of order → [discard | reorder up to N | error `[CODE]`]
- Maximum frequency: [N/s per session]; excess → [`RATE_LIMITED` error | silent discard]
- Maximum size: [bytes]

## Responses and errors

| Code | When | Client must |
|---|---|---|
| `[OK_xxx]` | | |
| `[ERR_xxx]` | | |

## Examples (fixtures in `protocol/examples/[name]/`)

- `valid-01.json` — [happy case]
- `invalid-01.json` — [missing field] → `[ERR_xxx]`
- `invalid-02.json` — [limit exceeded] → `[ERR_xxx]`

## Related legacy

- [FACT | HYPOTHESIS] [legacy subject/handler, file:line] — divergences: [PROPOSAL] [...]

## Compatibility

- Change: [minor | major] — reason: [...]
- Coexistence window: [simultaneously supported versions | cutover at `vX`]
