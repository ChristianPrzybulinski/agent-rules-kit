# Python recipes (agent-rules-kit, KIT-074), run from the profile folder. PYTHON names the interpreter the repository
# runs (default python3; on macOS a bare python3 can be the Xcode 3.9).

python := env('PYTHON', 'python3')

# pytest when the folder configures it, else stdlib unittest discovery in every folder holding a test_*.py
test:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -f pytest.ini ] || [ -f conftest.py ] || grep -qs '^\[tool\.pytest' pyproject.toml; then
      exec "{{python}}" -m pytest
    fi
    folders="$(find . -name 'test_*.py' -not -path '*/.*' -not -path '*/node_modules/*' -not -path '*/venv/*' \
      -exec dirname {} \; | sort -u)"
    [ -n "$folders" ] || { echo "just test: no test_*.py under this folder; a run with zero tests is a failure" >&2; exit 1; }
    while IFS= read -r folder; do
      "{{python}}" -B -m unittest discover -s "$folder" -t "$folder" -p 'test_*.py'
    done <<< "$folders"

# a syntax check of every .py (no bytecode written), then ruff check when the folder configures ruff
lint:
    #!/usr/bin/env bash
    set -euo pipefail
    "{{python}}" - <<'PY'
    import ast, pathlib, sys
    skip = {"node_modules", "venv", "__pycache__"}
    bad = 0
    for path in sorted(pathlib.Path(".").rglob("*.py")):
        if any(part.startswith(".") or part in skip for part in path.parts[:-1]):
            continue
        try:
            ast.parse(path.read_bytes(), str(path))
        except SyntaxError as err:
            print(f"{path}:{err.lineno}: {err.msg}")
            bad += 1
    sys.exit(1 if bad else 0)
    PY
    if [ -f ruff.toml ] || [ -f .ruff.toml ] || grep -qs '^\[tool\.ruff' pyproject.toml; then
      command -v ruff >/dev/null || { echo "just lint: ruff is configured but not on PATH" >&2; exit 1; }
      ruff check .
    fi

# ruff format when the folder configures ruff; the standard library has no formatter
fmt:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -f ruff.toml ] || [ -f .ruff.toml ] || grep -qs '^\[tool\.ruff' pyproject.toml; then
      exec ruff format .
    fi
    echo "just fmt: no formatter configured (ruff.toml, .ruff.toml or [tool.ruff] in pyproject.toml)" >&2
    exit 1

# the gate before a commit or PR
verify: lint test
