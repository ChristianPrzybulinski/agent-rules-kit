#!/usr/bin/env bash
# Scaffold for the eval case: a feature branch whose validation keeps a TODO and has no test.
set -euo pipefail
git init -q -b main .
git config user.email eval@example.invalid
git config user.name eval
mkdir -p src tests
printf 'def parse_age(text):\n    return int(text)\n' > src/validate.py
printf 'from src.validate import parse_age\n\ndef test_parse_age():\n    assert parse_age("7") == 7\n' > tests/test_validate.py
git add src tests
git commit -q -m 'feat: parse age'
git checkout -q -b feature/age-validation
printf 'def parse_age(text):\n    # TODO: reject negative ages\n    value = int(text)\n    if value > 150:\n        raise ValueError("age too large")\n    return value\n' > src/validate.py
git add src
git commit -q -m 'feat: validate age range'
