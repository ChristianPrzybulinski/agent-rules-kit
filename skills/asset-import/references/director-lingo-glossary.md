---
description: Macromedia/Adobe Director and Lingo glossary (cast, member, Score, ink, regPoint, Xtra, sendNetMessage/OpenSMUS) for reading the legacy archive. Load when analyzing Lingo code or a .dir/.cst inventory.
trigger: model_decision
verified: "2026-09-30"
sources:
  - https://help.adobe.com/archive/en_US/director/UsingScripting/director_reference.pdf
  - https://github.com/markhughes/opensmus
---

# Director / Lingo — glossary (legacy)


## Structure of a movie

- **cast / castLib**: the movie's media library; a movie can have several castLibs (internal + external `.cst`). In Lingo: `castLib("name")`, `member("n", "castLib")`.
- **member / memberNum**: a cast item (bitmap, text, script, sound, shape...). Referenced by name or number: `member("ball")`, `member(12, "interface")`.
- **Score**: the movie's timeline — a frames × channels grid where sprites are placed.
- **channel / sprite channel**: a Score track; a sprite occupies one channel over a frame range. `sprite(1).member`.
- **frame**: timeline unit; the playback head advances by frames (the movie runs at N fps); `go to frame "menu"`, `the frame`, `frameLabel`.
- **ink**: the sprite's compositing mode over the background. Common values: `Copy` (opaque, fast), `Matte` (removes white from the rectangle — used on sprites with a white background), `Background Transparent` (background-colored pixels become transparent).
- **regPoint (registration point)**: a bitmap member's reference point — where the sprite's `loc` anchors (center or corner). Affects alignment and rotation/flip.
- **palette**: indexed color palette (Director works with palettized images); `member.palette`, `the palette`.
- **Xtra**: extension plugin/binary (scripting, media, I/O, network). The `Multiuser Xtra` is what made the network connection. `[HYPOTHESIS]` the location of the Xtras used is in the archive manifests.

## Lingo — language

- **handler / `on` … `end`**: code block. `on mouseUp me ... end` = event handler; `on myMethod me, arg` = method/function.
- **`the`**: prefix for global/engine properties: `the frame`, `the itemDelimiter`, `the platform`, `the milliseconds`.
- **`me`**: reference to the current object/script (equiv. `this`) — appears in behaviors and parent scripts.
- **`global`**: declares a global variable: `global gScore`.
- **`property`**: instance field in a parent script/behavior: `property pSpeed`.
- **`itemDelimiter`**: separator character for `item n of string` expressions: `the itemDelimiter = ","`.
- **`sendNetMessage` / Multiuser Xtra**: sends a message to the Shockwave MultiUser Server (SMUS) — proprietary Macromedia/Adobe protocol. **OpenSMUS** is the 100% Java open-source server compatible with the SMUS protocol (a Shockwave movie connects unmodified; TCP and UDP from Director 8.5). Source: github.com/markhughes/opensmus.
- **File extensions**: `.dir` editable movie; `.cst` editable external cast; `.cxt` protected (compiled) cast; `.dcr` protected/published Shockwave movie. `[HYPOTHESIS]` `.dxr` = protected movie (same role as .dcr for disk files).
- **Script types**: behavior (bound to a sprite/frame in the Score), movie script (the movie's global handlers), parent script (object-oriented — `new(script "Person")`), cast member script (associated with the member).
