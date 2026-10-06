#!/usr/bin/env bash
# Scaffold for the eval case: a throwaway git repository in the empty workspace.
set -euo pipefail
git init -q .
git config user.email eval@example.invalid
git config user.name eval
printf 'config_version=5\n' > project.godot
printf 'extends Node\n' > main.gd
git add -A
git commit -q -m 'base'
