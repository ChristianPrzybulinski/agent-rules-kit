# Director / Lingo — glossário (legado)

Verificado: 2026-09-30. Fontes: Adobe Director Scripting Dictionary 11.5 (help.adobe.com/archive/en_US/director/UsingScripting/director_reference.pdf), Macromedia Director MX 2004 Scripting Reference, e github.com/markhughes/opensmus (README). Termos sem confirmação direta em fonte marcados `[HIPÓTESE]`.

## Estrutura de um movie

- **cast / castLib**: biblioteca de mídia do filme; um movie pode ter várias castLibs (interna + externas `.cst`). Em Lingo: `castLib("nome")`, `member("n", "castLib")`.
- **member / memberNum**: item do cast (bitmap, texto, script, sound, shape...). Referenciado por nome ou número: `member("bola")`, `member(12, "interface")`.
- **Score**: timeline do filme — grade de frames × channels onde sprites são posicionados.
- **channel / sprite channel**: uma faixa do Score; um sprite ocupa um channel por intervalo de frames. `sprite(1).member`.
- **frame**: unidade da timeline; o playback head avança por frames (movie roda a N fps); `go to frame "menu"`, `the frame`, `frameLabel`.
- **ink**: modo de composição do sprite sobre o fundo. Valores comuns: `Copy` (opaco, rápido), `Matte` (remove branco do retângulo — usado em sprites com fundo branco), `Background Transparent` (pixels da cor de fundo ficam transparentes).
- **regPoint (registration point)**: ponto de referência do member bitmap — onde o `loc` do sprite ancora (centro ou canto). Afeta alinhamento e rotação/flip.
- **palette**: paleta de cores indexada (Director trabalha com imagens palettized); `member.palette`, `the palette`.
- **Xtra**: plugin/binário de extensão (scripting, media, I/O, rede). O `Multiuser Xtra` é o que fazia conexão de rede. `[HIPÓTESE]` localização dos Xtras usados fica nos manifests do acervo.

## Lingo — linguagem

- **handler / `on` … `end`**: bloco de código. `on mouseUp me ... end` = handler de evento; `on meuMetodo me, arg` = método/função.
- **`the`**: prefixo para propriedades globais/engine: `the frame`, `the itemDelimiter`, `the platform`, `the milliseconds`.
- **`me`**: referência ao objeto/script atual (equiv. a `this`) — aparece em behaviors e parent scripts.
- **`global`**: declara variável global: `global gScore`.
- **`property`**: campo de instância em parent script/behavior: `property pSpeed`.
- **`itemDelimiter`**: caractere separador para expressões `item n of string`: `the itemDelimiter = ","`.
- **`sendNetMessage` / Multiuser Xtra**: envia mensagem ao Shockwave MultiUser Server (SMUS) — protocolo proprietário Macromedia/Adobe. **OpenSMUS** é o servidor open-source 100% Java compatível com o protocolo SMUS (movie Shockwave conecta sem modificação; TCP e UDP a partir do Director 8.5). Fonte: github.com/markhughes/opensmus.
- **Extensões de arquivo**: `.dir` movie editável; `.cst` cast externo editável; `.cxt` cast protegido (compilado); `.dcr` Shockwave movie protegido/publicado. `[HIPÓTESE]` `.dxr` = movie protegido (mesmo papel do .dcr para arquivos de disco).
- **Tipos de script**: behavior (ligado a sprite/frame no Score), movie script (handlers globais do filme), parent script (orientado a objeto — `new(script "Pessoa")`), cast member script (associado ao member).
