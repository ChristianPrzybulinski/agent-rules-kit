#!/usr/bin/env bash
# Scaffold for the eval case: a throwaway git repository in the empty workspace.
set -euo pipefail
git init -q .
git config user.email eval@example.invalid
git config user.name eval
printf 'items = []\n' > inventory.py
git add -A
git commit -q -m 'base'
git checkout -q -b feat/inventory-sort
printf 'items = sorted([])\n' > inventory.py
git commit -q -am 'feat: sort the inventory'
