#!/usr/bin/env bash
# Scaffold for the eval case: a repository with three worktrees under wt/.
# app-41: merged into main, clean. app-42: merged, dirty. app-43: not merged, clean.
set -euo pipefail
git init -q -b main .
git config user.email eval@example.invalid
git config user.name eval
printf 'wt/\n' > .gitignore
printf 'spawn = 1\n' > spawn.gd
printf 'loot = 1\n' > loot.gd
printf 'ui = 1\n' > ui.gd
git add -A
git commit -q -m 'base'
for n in 41 42 43; do
  case "$n" in 41) b=feature/FEAT-007-T1-spawn f=spawn.gd ;; 42) b=feature/FEAT-007-T2-loot f=loot.gd ;; 43) b=feature/FEAT-007-T3-ui f=ui.gd ;; esac
  git worktree add -q -b "$b" "wt/app-$n" main
  printf 'changed = %s\n' "$n" >> "wt/app-$n/$f"
  git -C "wt/app-$n" commit -q -am "feat: task $n"
done
git merge -q --no-ff -m 'Merge T1' feature/FEAT-007-T1-spawn
git merge -q --no-ff -m 'Merge T2' feature/FEAT-007-T2-loot
printf 'wip = true\n' >> wt/app-42/loot.gd
printf 'scratch\n' > wt/app-42/notes.txt
