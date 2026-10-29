#!/usr/bin/env bash
# Scaffold for the eval case: a throwaway git repository in the empty workspace.
set -euo pipefail
git init -q .
git config user.email eval@example.invalid
git config user.name eval
mkdir -p docs tools
printf '# Guide\n\nRun the sever with the defualt port.\n' > docs/guide.md
printf '#!/usr/bin/env bash\necho "40-minute suite"\n' > run-tests.sh
printf 'import sys\nprint("links OK", sys.argv[1:])\n' > tools/check_links.py
git add -A
git commit -q -m 'base'
printf '# Guide\n\nRun the server with the default port.\n' > docs/guide.md
git commit -q -am 'docs: fix two typos'
