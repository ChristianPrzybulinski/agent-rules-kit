---
description: JSON envelope codec over WebSocketPeer - validate-then-dispatch, sequence check, poll loop, heartbeat, reconnect and contract fixtures.
kind: fact
verified: "2026-10-06"
sources:
  - https://docs.godotengine.org/en/stable/classes/class_websocketpeer.html
  - https://docs.godotengine.org/en/stable/classes/class_json.html
  - https://godotengine.org/releases/4.4/
---

# Godot 4 - JSON envelope codec over WebSocketPeer

The envelope shape is the project's contract, fixed in its protocol repository. The parameters below exist in every contract of this kind:

- Parameter: envelope fields (for example `{v, type, id, seq, ts, payload}`); a `protocol_version` field on every envelope - a constant on the client, checked by the server; the first message after connect is where a mismatch surfaces.
- Parameter: per-connection sequence starting at 1 on each side, and a max inbound frame size in bytes.

## Decode: validate then dispatch

- Parse with `JSON.new().parse()`; require `data` to be a `Dictionary`.
- Check every envelope field exists with the right type; reject unknown fields.
- Check the inbound sequence is strictly greater than the last one seen.
- Only then `match` on `type` and validate that type's payload fields.
- A rejected frame emits a signal carrying the reason and is never partially applied.

## Peer loop and heartbeat

- In `_process`: `poll()`, read `get_ready_state()`, drain `get_available_packet_count()` while `STATE_OPEN` or `STATE_CLOSING`; emit connect/disconnect from state transitions only.
- Heartbeat: `heartbeat_interval` sends WebSocket ping frames (see `./networking-transports.md`); the property exists since Godot 4.4. The server's ping/timeout values are project parameters.

## Reconnect

- Exponential backoff with jitter and a cap; emit each attempt as a signal so the UI can show it.
- Reset all codec state (sequences, outstanding ids, handshake flags) on every new connection.
- After reconnect, restore state from the server snapshot; never replay unacknowledged commands without the contract's dedup rule.

## Fixtures

- The contract repository's `valid/<type>/*.json` and `invalid/<type>/*.json` are the client's test inputs: every valid example must parse ok, every invalid scenario must be rejected.
- Parameter: copies live in the client repo under `tests/fixtures/protocol/` by default - synced from the contract repository, never hand-written.
