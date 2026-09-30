# Godot 4 — transportes de rede (cliente Godot ↔ servidor não-Godot)

Verificado: 2026-09-30. Fontes: docs.godotengine.org/en/stable (Godot 4.7). Nota factual — não é recomendação; a escolha é DEC do projeto. Todas as classes abaixo existem nos exports Windows/macOS (desktop não tem restrição de plataforma; a nota de permissão `INTERNET` só vale para Android).

## `StreamPeerTCP` — TCP raw

- Classe: `StreamPeerTCP` (StreamPeer ← RefCounted). `connect_to_host(host, port)`, `poll()`, `put_data`/`get_data` ou via `StreamPeerBuffer`. Doc: https://docs.godotengine.org/en/stable/classes/class_streampeertcp.html
- Confiabilidade/ordem: sim (TCP).
- TLS: a classe em si é plain; TLS vem de `StreamPeerTLS.connect_to_stream(stream, hostname, TLSOptions)` embrulhando o TCP — https://docs.godotengine.org/en/stable/classes/class_streampeertls.html
- Lado Java: `java.net` ServerSocket/Socket ou NIO — protocolo de aplicação totalmente sob responsabilidade do projeto (framing, serialização).

## `WebSocketPeer` — WebSocket (RFC 6455)

- Classe: `WebSocketPeer` (PacketPeer). `connect_to_url(url, tls_client_options)`, `poll()`, frames binários via `put_packet`/`send`, texto via `send_text`; heartbeat embutido (`heartbeat_interval`). Doc: https://docs.godotengine.org/en/stable/classes/class_websocketpeer.html
- Confiabilidade/ordem: sim (roda sobre TCP).
- TLS: sim, `wss://` com `TLSOptions`.
- Lado Java: protocolo padrão — Jakarta WebSocket (servidor, ex.: Tyrus), Spring WebSocket, ou qualquer servidor RFC 6455.

## `ENetConnection` — ENet sobre UDP

- Classe: `ENetConnection` (wrapper de `ENetHost`). `create_host`, `connect_to_host`, `service()`, eventos CONNECT/DISCONNECT/RECEIVE, canais, compressão (range coder, FastLZ, zlib, zstd). Funciona sem `MultiplayerAPI` (ENet puro). Doc: https://docs.godotengine.org/en/stable/classes/class_enetconnection.html
- Confiabilidade/ordem: por pacote — ENet oferece flags reliable/unreliable e ordenação por canal (http://enet.bespin.org/usergroup0.html).
- TLS: DTLS — `dtls_client_setup(hostname, TLSOptions)` / `dtls_server_setup` (mesma doc).
- Lado Java: ENet é protocolo próprio; não há implementação no JDK — exige biblioteca/binding ENet para Java (ecossistema pequeno) `[HIPÓTESE: confirmar opções Java na Fase 2]`.

## `PacketPeerUDP` — UDP raw

- Classe: `PacketPeerUDP` (PacketPeer). `bind`, `connect_to_host` (filtra origem — "não envia dados"), `set_dest_address`, multicast, broadcast. Doc: https://docs.godotengine.org/en/stable/classes/class_packetpeerudp.html
- Confiabilidade/ordem: não (UDP puro; a própria doc sugere TLS/DTLS para dados sensíveis).
- TLS: não diretamente; DTLS via `PacketPeerDTLS`/`DTLSServer` (classes existem na doc).
- Lado Java: `java.net.DatagramSocket`; confiabilidade/ordem/retry sob responsabilidade do protocolo do projeto.

## `HTTPRequest` / `HTTPClient` — HTTP(S)

- `HTTPRequest` (Node): request/response HTTP alto nível, `TLSOptions` no construtor/request → HTTPS. `HTTPClient` (low-level) para controle fino (chunked, status manual). Docs: https://docs.godotengine.org/en/stable/classes/class_httprequest.html e .../class_httpclient.html
- Confiabilidade/ordem: sim (TCP+TLS); sem conexão persistente de mensagens — request/response.
- TLS: sim (HTTPS), incl. certificado customizado via `TLSOptions`.
- Lado Java: qualquer servidor HTTP (Spring Boot). Uso típico: auth, API REST, assets — não canal de gameplay em tempo real.
