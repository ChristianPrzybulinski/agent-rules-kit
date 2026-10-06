#!/usr/bin/env bash
# Scaffold for the eval case: a throwaway git repository in the empty workspace.
set -euo pipefail
git init -q .
git config user.email eval@example.invalid
git config user.name eval
printf 'def add(a, b):\n    return a - b\n' > calc.py
printf 'import calc\nassert calc.add(2, 3) == 5, "add(2, 3) must be 5"\n' > test_calc.py
git add -A
git commit -q -m 'base'
