# kit git-lfs

Ready-made `.gitattributes` for projects with art/binaries (Godot 2D in particular).

## Usage

1. Copy `.gitattributes` to the repo root **before** the first binary enters — adding it later requires `git lfs migrate` (rewrites history).
2. `git lfs install` (once per machine). Fresh clone: `git lfs install && git lfs pull`.
3. New binary type → add the pattern **in the same commit** as the first file.

Full rules: `skills/git-lfs/references/git-lfs-and-binaries.md`. GitHub quotas: `skills/git-lfs/references/lfs-quotas-github.md`.
