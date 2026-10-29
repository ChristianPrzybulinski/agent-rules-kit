#!/usr/bin/env bash
# Scaffold for the eval case: a throwaway git repository in the empty workspace.
set -euo pipefail
git init -q .
git config user.email eval@example.invalid
git config user.name eval
printf 'timeout = 30\n' > login.cfg
git add -A
git commit -q -m 'base'
git checkout -q -b fix/login-timeout
printf 'timeout = 60\n' > login.cfg
git commit -q -am 'fix: raise the login timeout'
