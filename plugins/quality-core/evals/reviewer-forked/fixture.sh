#!/usr/bin/env bash
# Scaffold for the eval case: a throwaway git repository in the empty workspace.
set -euo pipefail
git init -q .
git config user.email eval@example.invalid
git config user.name eval
printf 'def greet():\n    return "hello"\n' > greet.py
git add -A
git commit -q -m 'base'
