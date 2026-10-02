---
name: git-lfs
version: "1.1"
description: Git LFS policy. Use when editing .gitattributes, adding/migrating a large binary or checking quota. Not for branch policy (skill branching-and-versioning).
argument-hint: "[init | audit | migrate <pattern>]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - exec
  - edit
---

# Git LFS

Read `references/git-lfs-and-binaries.md` for file policy and `references/lfs-quotas-github.md` for current quota facts.

## 1. Classify before adding

Add the binary pattern to root `.gitattributes` before the first file. Script-generated output is not versioned when the script plus manifest can reproduce it; use LFS with that manifest only when generation exceeds five minutes or CI lacks the tool.

## 2. Initialize tracking

Run `git lfs install --local`, update `.gitattributes`, commit it before binaries and verify with `git lfs track`. Godot versions `*.import` but never `.godot/`.

## 3. Audit storage and quota

- Run `git lfs status` and `git lfs ls-files -s`.
- Find tracked files over 1 MB whose `git check-attr filter` is not `lfs`; stop before commit.
- Sum LFS sizes and compare with the referenced GitHub quota; warn above 70%.

## 4. Migrate existing history safely

Preview with `git lfs migrate info --everything --include=<patterns>`. Migration rewrites history: ask before execution when any remote/shared clone exists. If explicitly authorized, import then push the feature branch with `--force-with-lease`; never rewrite `main` by default.

## 5. Report

List installed state, `.gitattributes` gaps, escaped files with sizes, estimated usage/quota and the next required action.

Done when: patterns precede binaries, generated artifacts follow script+manifest policy, no large file escapes LFS and any history rewrite has explicit authorization.
