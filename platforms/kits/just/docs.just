# Spec recipes (agent-rules-kit, KIT-074). They run the installed kit's validators and schemas (KIT-081 stage 1: no
# copy in the project), ${AI_KIT_DIR:-$HOME/.ai-kit}/platforms/ci/, from the repository root wherever the module sits.
# PYTHON names the interpreter (default python3).

python := env('PYTHON', 'python3')

# check_spec.py on docs/spec, spec_trace.py check, and check_docs_structure.py (it passes as "off" unless enabled)
lint:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "$(git rev-parse --show-toplevel)"
    kit="${AI_KIT_DIR:-$HOME/.ai-kit}/platforms/ci"
    if [ ! -f "$kit/validations/check_spec.py" ]; then
      echo "lint: no agent-rules-kit spec tools in ${AI_KIT_DIR:-$HOME/.ai-kit}; set AI_KIT_DIR to the kit or run its platforms/tools/bootstrap.sh" >&2
      exit 1
    fi
    "{{python}}" -B "$kit/validations/check_spec.py" docs/spec "$kit/schemas"
    "{{python}}" -B "$kit/validations/spec_trace.py" check docs/spec
    "{{python}}" -B "$kit/validations/check_docs_structure.py"

# the gate before a commit or PR
verify: lint

# move the changelog.d fragments into CHANGELOG.md → ## [Unreleased] (KIT-084); `just changelog --check` writes nothing
changelog *ARGS:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "$(git rev-parse --show-toplevel)"
    tool="${AI_KIT_DIR:-$HOME/.ai-kit}/platforms/ci/validations/changelog_fragments.py"
    if [ ! -f "$tool" ]; then
      echo "changelog: no agent-rules-kit changelog tool in ${AI_KIT_DIR:-$HOME/.ai-kit}; set AI_KIT_DIR to a kit with KIT-084 or run its platforms/tools/bootstrap.sh" >&2
      exit 1
    fi
    "{{python}}" -B "$tool" --repo-dir . {{ARGS}}
