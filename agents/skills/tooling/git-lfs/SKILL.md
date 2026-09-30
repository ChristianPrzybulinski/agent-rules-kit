---
name: git-lfs
version: "1.0"
description: Configures and audits Git LFS in a repository — .gitattributes by type/size, migrating already-committed binaries, quota verification and files that escaped LFS. Use when starting a repo with assets, adding a new binary type, or when `git status` shows a large binary.
argument-hint: "[init | audit | migrate <pattern>]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - exec
---

# Git LFS

Policy in `agents/rules/git/git-lfs-and-binaries.md`. `.gitattributes` template in `platforms/kits/git-lfs/`.

## init (new repo or no LFS)

1. `git lfs install --local` (does not change global config).
2. Copy `platforms/kits/git-lfs/.gitattributes` to the root; adjust patterns to the project (Godot: keep `*.import` out of LFS).
3. Commit `.gitattributes` **before** any binary: `git add .gitattributes && git commit -m "chore: configure Git LFS"`.
4. Verify: `git lfs track` lists the patterns.

## audit

```bash
git lfs ls-files -s | sort -k3 -h | tail        # largest in LFS
git lfs status                                   # pending
git ls-files -z | xargs -0 -I{} sh -c 'test $(stat -f%z "{}") -gt 1048576 && echo "{}"' \
  | while read f; do git check-attr filter "$f" | grep -q lfs || echo "OUTSIDE LFS: $f"; done
```
Files >1 MB outside LFS → list with size. Quota (GitHub Free/Pro: 10 GiB storage + 10 GiB bandwidth/month; source in `agents/knowledge/git/lfs-quotas-github.md`): `git lfs ls-files -s` summed; >70% → warn.

## migrate (binary already committed without LFS)

Rewrites history. **Ask first** if the repo has a remote with other clones.
```bash
git lfs migrate info --everything --include="*.png,*.wav"     # preview
git lfs migrate import --everything --include="*.png,*.wav"   # execute
git push --force-with-lease origin main                      # only with explicit authorization
```

## Verdict

```
LFS: installed | not installed
.gitattributes: OK | missing | incomplete (missing: ...)
Outside LFS (>1MB): <list or none>
Estimated usage: N MB (GitHub Free quota 10 GiB)
Next step: ...
```
