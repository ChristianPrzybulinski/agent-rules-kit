---
description: "Godot 4 transport facts for TCP, WebSocket, ENet, UDP and HTTP. Load when comparing client/server reliability and TLS."
kind: fact
verified: "2026-09-30"
sources:
  - https://docs.godotengine.org/en/stable/classes/class_websocketpeer.html
  - https://docs.godotengine.org/en/stable/classes/class_enetconnection.html
  - https://docs.godotengine.org/en/stable/classes/class_streampeertcp.html
  - https://docs.godotengine.org/en/stable/classes/class_packetpeerudp.html
  - https://docs.godotengine.org/en/stable/classes/class_httprequest.html
---

# Godot 4 — transports (Godot client ↔ non-Godot server)

Factual note, not a recommendation — the choice is a project DEC. All classes exist in Windows/macOS exports (the `INTERNET` permission only applies to Android).

| Option | Reliable/ordered | TLS | Java side |
|---|---|---|---|
| `StreamPeerTCP` (raw TCP) | yes (TCP) | via `StreamPeerTLS.connect_to_stream` | ServerSocket/NIO; framing and serialization 100% the project's |
| `WebSocketPeer` (RFC 6455) | yes (TCP) | yes, `wss://` + `TLSOptions` | standard: Jakarta WebSocket (Tyrus), Spring WebSocket |
| `ENetConnection` (ENet/UDP, without MultiplayerAPI) | per packet: reliable/unreliable flags, per-channel ordering | DTLS (`dtls_client_setup`) | requires an ENet lib/binding for Java — small ecosystem `[HYPOTHESIS: confirm in Phase 2]` |
| `PacketPeerUDP` (raw UDP) | no | no; DTLS via `PacketPeerDTLS` | `DatagramSocket`; reliability/ordering/retry are the project's |
| `HTTPRequest`/`HTTPClient` | yes (TCP), request/response without a persistent channel | yes (HTTPS) | any HTTP (Spring Boot) — auth, REST, assets |

ENet: per-host compression (range coder, FastLZ, zlib, zstd), CONNECT/DISCONNECT/RECEIVE events, channels — doc `class_enetconnection`.
`WebSocketPeer`: built-in heartbeat (`heartbeat_interval`); `send_text`/binary frames.
