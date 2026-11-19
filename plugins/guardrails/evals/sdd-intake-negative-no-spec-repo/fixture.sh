#!/usr/bin/env bash
# Scaffold for the eval case: a plain repository with no docs/spec/ and a function that crashes on an empty list.
set -euo pipefail
git init -q -b main .
git config user.email eval@example.invalid
git config user.name eval
mkdir -p src tests
printf 'def export_rows(rows):\n    header = sorted(rows[0].keys())\n    return [header] + [[row[key] for key in header] for row in rows]\n' > src/export.py
printf 'from src.export import export_rows\n\ndef test_export_rows():\n    assert export_rows([{"a": 1}]) == [["a"], [1]]\n' > tests/test_export.py
git add src tests
git commit -q -m 'base'
