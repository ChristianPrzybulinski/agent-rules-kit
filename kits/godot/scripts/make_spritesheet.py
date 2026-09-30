#!/usr/bin/env python3
"""Monta uma spritesheet a partir de PNGs nomeados <x>_<nn>.png.

Uso: make_spritesheet.py <dir-de-frames> <saida.png>
Gera <saida.png> e <saida>.manifest.json com frames, tamanho, ordem e sha256.

Requer Pillow: pip3 install --user pillow
"""
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow nao instalado. Instale com: pip3 install --user pillow")

FRAME_RE = re.compile(r"^(.+?)_(\d+)\.png$", re.IGNORECASE)


def main() -> int:
    if len(sys.argv) != 3:
        sys.exit(f"uso: {sys.argv[0]} <dir-de-frames> <saida.png>")
    src, out = Path(sys.argv[1]), Path(sys.argv[2])

    frames = []
    for f in sorted(src.glob("*.png")):
        m = FRAME_RE.match(f.name)
        if m:
            frames.append((int(m.group(2)), f))
    if not frames:
        sys.exit(f"nenhum frame <nome>_<nn>.png em {src}")
    frames.sort()

    images = [Image.open(f) for _, f in frames]
    w, h = images[0].size
    if any(im.size != (w, h) for im in images):
        sys.exit("frames com tamanhos diferentes; spritesheet exige tamanho uniforme")

    sheet = Image.new("RGBA", (w * len(images), h))
    manifest_frames = []
    for i, ((num, f), im) in enumerate(zip(frames, images)):
        sheet.paste(im, (i * w, 0))
        manifest_frames.append({
            "index": i,
            "file": f.name,
            "number": num,
            "x": i * w,
            "y": 0,
            "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
        })
    sheet.save(out)

    import PIL
    manifest = {
        "sheet": out.name,
        "frame_size": {"w": w, "h": h},
        "frame_count": len(images),
        "order": [f.name for _, f in frames],
        "frames": manifest_frames,
        "tool": f"make_spritesheet.py (Pillow {PIL.__version__})",
    }
    out.with_suffix(out.suffix + ".manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"{out} ({len(images)} frames de {w}x{h})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
