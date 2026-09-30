---
description: "Transportes cliente↔servidor em Godot 4 com servidor não-Godot (StreamPeerTCP, WebSocketPeer, ENetConnection, PacketPeerUDP, HTTPRequest): confiabilidade, TLS, exigência no lado Java. Carregar ao decidir/decodificar transporte."
trigger: model_decision
verified: "2026-09-30"
sources:
  - https://docs.godotengine.org/en/stable/classes/class_websocketpeer.html
  - https://docs.godotengine.org/en/stable/classes/class_enetconnection.html
  - https://docs.godotengine.org/en/stable/classes/class_streampeertcp.html
  - https://docs.godotengine.org/en/stable/classes/class_packetpeerudp.html
  - https://docs.godotengine.org/en/stable/classes/class_httprequest.html
---

# Godot 4 — transportes (cliente Godot ↔ servidor não-Godot)

Nota factual, não recomendação — a escolha é DEC do projeto. Todas as classes existem nos exports Windows/macOS (a permissão `INTERNET` só vale para Android).

| Opção | Confiável/ordenado | TLS | Lado Java |
|---|---|---|---|
| `StreamPeerTCP` (TCP raw) | sim (TCP) | via `StreamPeerTLS.connect_to_stream` | ServerSocket/NIO; framing e serialização 100% do projeto |
| `WebSocketPeer` (RFC 6455) | sim (TCP) | sim, `wss://` + `TLSOptions` | padrão: Jakarta WebSocket (Tyrus), Spring WebSocket |
| `ENetConnection` (ENet/UDP, sem MultiplayerAPI) | por pacote: flags reliable/unreliable, ordem por canal | DTLS (`dtls_client_setup`) | exige lib/binding ENet p/ Java — ecossistema pequeno `[HIPÓTESE: confirmar na Fase 2]` |
| `PacketPeerUDP` (UDP raw) | não | não; DTLS via `PacketPeerDTLS` | `DatagramSocket`; confiabilidade/ordem/retry do projeto |
| `HTTPRequest`/`HTTPClient` | sim (TCP), request/response sem canal persistente | sim (HTTPS) | qualquer HTTP (Spring Boot) — auth, REST, assets |

ENet: compressão por host (range coder, FastLZ, zlib, zstd), eventos CONNECT/DISCONNECT/RECEIVE, canais — doc `class_enetconnection`.
`WebSocketPeer`: heartbeat embutido (`heartbeat_interval`); `send_text`/frames binários.
