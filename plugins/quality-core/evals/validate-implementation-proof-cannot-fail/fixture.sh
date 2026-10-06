#!/usr/bin/env bash
# Scaffold for the eval case: a throwaway git repository in the empty workspace.
set -euo pipefail
git init -q .
git config user.email eval@example.invalid
git config user.name eval
mkdir -p tests
touch tests/.gitkeep
cat > run_tests.sh <<'SH'
#!/bin/sh
# runs every test under tests/
for t in tests/*_test.sh; do
  [ -f "$t" ] && sh "$t"
done
exit 0
SH
git add -A
git commit -q -m 'base'
