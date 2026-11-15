# Spec recipes (agent-rules-kit, KIT-074). They run the copies platforms/tools/sync-project.sh vendors into
# .github/spec-lint/, from the repository root wherever the module sits. PYTHON names the interpreter (default python3).

python := env('PYTHON', 'python3')

# check_spec.py on docs/spec, spec_trace.py check when journeys are on, check_docs_structure.py when vendored
lint:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "$(git rev-parse --show-toplevel)"
    "{{python}}" -B .github/spec-lint/check_spec.py docs/spec .github/spec-lint/schemas
    if [ -f .github/spec-lint/spec_trace.py ]; then "{{python}}" -B .github/spec-lint/spec_trace.py check docs/spec; fi
    if [ -f .github/spec-lint/check_docs_structure.py ]; then "{{python}}" -B .github/spec-lint/check_docs_structure.py; fi

# the gate before a commit or PR
verify: lint
