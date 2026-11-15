#!/usr/bin/env bash
# Scaffold for the eval case: a repository with three independent check scripts.
set -euo pipefail
git init -q -b main .
mkdir -p scripts
printf '#!/bin/sh\nsleep 2\necho "tests: 41 passed, 1 failed (test_total_rounds)"\nexit 1\n' > scripts/test.sh
printf '#!/bin/sh\nsleep 1\necho "lint: 2 warnings in src/cart.py"\n' > scripts/lint.sh
printf '#!/bin/sh\nsleep 1\necho "types: 0 errors"\n' > scripts/typecheck.sh
chmod +x scripts/*.sh
printf '# cart\n\nChecks: `scripts/test.sh` (about 8 minutes on CI), `scripts/lint.sh`, `scripts/typecheck.sh`.\n' > README.md
