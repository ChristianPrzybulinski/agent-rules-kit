# Godot 4 recipes (agent-rules-kit, KIT-074), run from the Godot project folder (the one with project.godot).
# GODOT names the binary (default godot); GODOT_TEST_RUNNER picks gdunit4 (default) or gut.

godot := env('GODOT', 'godot')
test_runner := env('GODOT_TEST_RUNNER', 'gdunit4')

# open the editor
editor:
    {{godot}} --path . --editor

# run the game; arguments reach it after -- (just run --server-url=ws://127.0.0.1:8080/ws)
run *ARGS:
    {{godot}} --path . -- {{ARGS}}

# import assets and build the script-class cache (a fresh checkout needs it before boot and test)
import:
    {{godot}} --headless --path . --import

# boot proof: godot --quit exits 0 after a script error, so the log decides
boot: import
    #!/usr/bin/env bash
    set -euo pipefail
    log="$(mktemp)"
    {{godot}} --headless --path . --quit 2>&1 | tee "$log"
    if grep -Eq "SCRIPT ERROR|Parse Error|Parser Error|Can't load script" "$log"; then
      echo "just boot: the boot log holds a script error" >&2
      exit 1
    fi

# the unit suite after an import; a missing runner, no suite or zero executed test cases fails, as in CI
test: import
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{test_runner}}" in
      gdunit4)
        [ -d addons/gdUnit4 ] || { echo "just test: addons/gdUnit4 missing; tests are never skipped" >&2; exit 1; }
        # a command substitution, not a pipe: with pipefail an early grep -q exit can fail the writer
        if [ -z "$(find tests -name '*_test.gd' -print -quit 2>/dev/null)" ]; then
          echo "just test: no gdUnit4 suite (*_test.gd) under tests/; a green run with zero tests is a failure" >&2
          exit 1
        fi
        log="$(mktemp)"
        {{godot}} --headless --path . -s addons/gdUnit4/bin/GdUnitCmdTool.gd -a res://tests -c --ignoreHeadlessMode \
          | tee "$log"
        esc="$(printf '\033')"
        if ! grep -Eq 'Overall Summary: [1-9][0-9]* test cases' <<< "$(sed "s/${esc}\[[0-9;]*m//g" "$log")"; then
          echo "just test: gdUnit4 executed no test case; check the runner and the import" >&2
          exit 1
        fi
        ;;
      gut)
        [ -d addons/gut ] || { echo "just test: addons/gut missing; tests are never skipped" >&2; exit 1; }
        if [ -z "$(find test tests -name 'test_*.gd' -print -quit 2>/dev/null)" ]; then
          echo "just test: no GUT suite (test_*.gd) under test/ or tests/" >&2
          exit 1
        fi
        {{godot}} --headless --path . -s addons/gut/gut_cmdln.gd -gdir=res://test,res://tests -ginclude_subdirs -gexit
        ;;
      *)
        echo "just test: unknown GODOT_TEST_RUNNER '{{test_runner}}' (gdunit4 or gut)" >&2
        exit 1
        ;;
    esac

# gdformat --check and gdlint on the project's scripts (addons/ and .godot/ left out)
lint:
    #!/usr/bin/env bash
    set -euo pipefail
    list="$(mktemp)"
    find . -name '*.gd' -not -path './addons/*' -not -path './.godot/*' -print0 > "$list"
    [ -s "$list" ] || { echo "just lint: no .gd file outside addons/ and .godot/" >&2; exit 1; }
    xargs -0 gdformat --check < "$list"
    xargs -0 gdlint < "$list"

# gdformat on the project's scripts (addons/ and .godot/ left out)
fmt:
    #!/usr/bin/env bash
    set -euo pipefail
    find . -name '*.gd' -not -path './addons/*' -not -path './.godot/*' -print0 | xargs -0 gdformat

# the gate before a commit or PR: lint, boot proof, unit suite
verify: lint boot test

# export a preset (export templates and export_presets.cfg needed): just export "Windows Desktop" build/game.exe
export PRESET OUT:
    {{godot}} --headless --path . --export-release "{{PRESET}}" "{{OUT}}"
