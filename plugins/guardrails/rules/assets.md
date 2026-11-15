---
description: Always/never constraints for art brought into a Godot project; the batch manifest, transforms and sprite-sheet tool are in the sdd-implement assets reference.
trigger: glob
globs:
  - "**/assets/**"
  - "**/*.png"
paths:
  - "**/assets/**"
  - "**/*.png"
---

Always/never for sprites, tilesets and maps brought into a Godot project. The batch manifest fields, the stages, the sprite-sheet tool and the recovery report: skill `sdd-implement`, reference `assets.md`.

- Never: change an original; keep it read-only and record each source's path, SHA-256 and license; stop on a hash mismatch instead of choosing between divergent copies.
- Always: read `.gitattributes`, known archive gaps and the `git-lfs-and-binaries` reference in skill `git` before producing a binary.
- Always: every derived file has a batch manifest row that points back to its prior stage (originals, normalized, derived, Godot-imported); identical hashes share one derivative and keep every alias, a divergent pair gets `status: review`.
- Always: without review, only lossless steps: rename, organize, lossless conversion, a crop from existing metadata, assembling already-identified frames. A color key, pivot change, scaling, frame order or inferred timing or direction needs a recorded decision; a color key is per batch with its color, tolerance and a before/after preview, never global.
- Always: only the batch the FEAT needs goes under `res://`; never copy the archive.
- Always: pixel-art filtering and mipmaps are set once at project import level, never per sprite.
- Always: atlases, tilesets and `SpriteFrames` come from a reproducible script whose command and output hashes the manifest records; run it twice and compare the hashes.
- Never: distribute an asset with missing provenance or license; that is a blocker.
