---
description: "Godot asset import: manifest fields, stages, approved transforms and the report. Load when importing art."
kind: detail
---

# Asset import

A task that brings sprites, tilesets or maps into a Godot project. Always/never (originals read-only, approved transforms, reproducible output, provenance): rule `assets.md`. Drawing or retouching art is out of scope. The assets to import are the rows of the FEAT's Plan § Assets when the project lists that section (`../../sdd-plan/references/plan-sections.md`); each row's source and license start the provenance below.

## 1. Establish provenance

- Keep originals read-only; record each source path, SHA-256 and usage license.
- Read the `git-lfs-and-binaries` reference in skill `git`, `.gitattributes` and the known archive gaps before producing files.
- Stop on an input hash mismatch; never silently choose between divergent source copies.

## 2. Define the batch manifest

Track `origin_path, origin_sha256, origin_group, origin_index, name, aliases, width, height, pivot_x, pivot_y, origin_format, derived_path, derived_sha256, transformations, status, reason`.

- Stages are originals → normalized → derived → Godot-imported; every row points back to the prior stage.
- Identical hashes share one derivative and preserve all aliases; divergent pairs use `status: review`.

## 3. Apply only approved transforms

- Without review: rename, organize, lossless conversion, crop from existing metadata, or assemble already-identified frames.
- With a recorded decision or manifest decision: color-key removal, pivot changes, scaling, frame ordering, or inferred timing or direction.
- A color key is per batch with explicit color, tolerance and a before/after preview; never global.

## 4. Produce Godot assets

- Put only the batch the FEAT needs under `res://`; do not copy the archive.
- Configure pixel-art filtering and mipmaps at project import level.
- Generate atlases, tilesets or `SpriteFrames` with a reproducible script and record its command and hashes.
- A sprite sheet built from exported frames follows the line above (a reproducible script, its command and the hashes recorded); record `hframes`/`vframes` and the pivot in the batch manifest.

## 5. Verify and report

- Run the generation twice and compare bytes by hash.
- Write a recovery report with input/ok/rejected/review counts, preview paths and unverified items.
- Missing provenance or license is a distribution blocker.

Done when: originals are unchanged, every output has a manifest chain and a stable hash, and review and rejected items are explicit.
