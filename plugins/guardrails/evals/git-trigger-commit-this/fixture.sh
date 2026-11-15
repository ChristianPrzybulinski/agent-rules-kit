#!/usr/bin/env bash
# Scaffold for the eval case: a repository with one commit and an uncommitted rename.
set -euo pipefail
git init -q -b main .
git config user.email eval@example.invalid
git config user.name eval
mkdir -p src
printf 'def get_user(user_id):\n    return {"id": user_id}\n' > src/users.py
printf 'from users import get_user\n\nprint(get_user(1))\n' > src/main.py
git add src
git commit -q -m 'feat(users): add the users module'
printf 'def fetch_user(user_id):\n    return {"id": user_id}\n' > src/users.py
printf 'from users import fetch_user\n\nprint(fetch_user(1))\n' > src/main.py
