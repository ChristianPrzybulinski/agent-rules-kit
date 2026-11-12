#!/usr/bin/env bash
# Scaffold for the eval case: a throwaway git repository in the empty workspace.
set -euo pipefail
git init -q .
git config user.email eval@example.invalid
git config user.name eval
mkdir -p src
printf 'extends Node\n# TODO: validate input\n# TODO: log errors\n# TODO: handle timeout\n' > src/app.gd
git add -A
git commit -q -m 'base'
