---
name: asset-import
description: Godot asset import with manifests and reproducible transforms. Use when bringing sprites, tilesets or maps into Godot. Not for drawing art (skill krita).
argument-hint: "[batch: path to originals | FEAT-xxx]"
triggers:
  - user
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# Asset Import

Reference: `references/director-lingo-glossary.md` for Director/Lingo archive terms.

## 1. Establish provenance

- Keep originals read-only; record each source path, SHA-256 and usage license.
- Read `../git-lfs/references/git-lfs-and-binaries.md`, `.gitattributes` and known archive gaps before producing files.
- Stop on an input hash mismatch; do not silently choose between divergent source copies.

## 2. Define the batch manifest

Track `origin_path, origin_sha256, cast, number, name, aliases, width, height, pivot_x, pivot_y, origin_format, derived_path, derived_sha256, transformations, status, reason`.

- Stages are originals → normalized → derived → Godot-imported; every row points back to the prior stage.
- Identical hashes share one derivative and preserve all aliases; divergent pairs use `status: review`.

## 3. Apply only approved transforms

- Without review: rename, organize, lossless conversion, crop from existing metadata, or assemble already-identified frames.
- With a recorded DEC or manifest decision: color-key removal, pivot changes, scaling, frame ordering, or inferred timing/direction.
- A color key is per batch with explicit color, tolerance and before/after preview; never global.

## 4. Produce Godot assets

- Put only the batch needed by the FEAT under `res://`; do not copy the archive.
- Configure pixel-art filtering and mipmaps at project import level.
- Generate atlases, tilesets or `SpriteFrames` with a reproducible script and record its command and hashes.

## 5. Verify and report

- Run the generation twice and compare bytes by hash.
- Write `../../templates/doc-recovery-report.md` with input/ok/rejected/review counts, preview paths and unverified items.
- Missing provenance or license is a distribution blocker.

Done when: originals are unchanged, every output has a manifest chain and stable hash, and review/rejected items are explicit.
