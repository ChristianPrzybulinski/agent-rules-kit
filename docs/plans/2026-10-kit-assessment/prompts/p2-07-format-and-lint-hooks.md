# P2-07 — Format and lint hooks (PostToolUse) for GDScript, Java and spec

Phase: 2 · Repos: kit · Branch to create: feat/p2-07-format-and-lint-hooks from main · Depends on: P1-07, P2-02 (same `check_kit.py`; P2-02 changes one constant on line 28 and no line count) · Effort: ~5 h

## Goal

Add one PostToolUse hook to `plugins/core/hooks/hooks.json` that runs after every Edit or Write: `gdformat` then `gdlint` for `*.gd`, `google-java-format --replace` for `*.java`, and the project's synced `.github/spec-lint/check_spec.py` for `docs/spec/**/*.md`. The hook fails open (exit 0 plus a one-line notice) when the tool is absent and surfaces findings to the agent (exit 2, findings on stderr) when a tool reports problems. Extend `check_kit.py` so the validator accepts PostToolUse and runs a deterministic case table against the hook with stub tools, exactly as it already does for the PreToolUse guard. Measurable result: `check_kit.py` runs at least 10 PostToolUse cases in CI, and piping a PostToolUse payload for a `.gd`, `.java` or `docs/spec/` file into the command yields the documented exit code and message in every branch.

## Why

- assessment §6 item C2: a PostToolUse hook on `Edit|Write` running `gdformat`/`gdlint`, `google-java-format` (faster than `spotless:apply` per edit) and `check_spec.py` is "Anthropic's number one example for hooks and eliminates the \"formatting\" finding class from reviews" (assessment.md:262).
- assessment §5, hooks rows: "what must always hold goes to a PreToolUse hook" is rated partial, and the JSON contract row records that `decision: block` belongs to PostToolUse/Stop while the guard relies on exit 2; today the kit has no hook of any kind after an edit (`plugins/core/hooks/hooks.json:3-14` holds only `PreToolUse`).
- The validator forbids the event: `platforms/ci/validations/check_kit.py:452` is `unknown_events = set(hook_events) - {"PreToolUse"}`, and `:485-486` rejects any `timeout > 10`. A formatter plus a JVM start (google-java-format) or a 130-artifact spec check (measured 1.0 s on stratics-docs, `spec: OK (130 artifacts)`) needs a higher ceiling.
- Consumers have the inputs: stratics-client has 18 project `.gd` files (236 more under `addons/`, which the hook formats too unless P3-02's config excludes them) and no `gdlintrc`; stratics-server has 454 `.java` files formatted by Spotless with google-java-format 1.30.0 (`pom.xml:170-183`), while the kit parent pins `google-java-format.version` 1.36.1 (`platforms/kits/java-maven/pom-parent.xml:21`); stratics-docs carries `.github/spec-lint/check_spec.py` and `schemas/` synced from the kit.
- Claude Code docs (code.claude.com/docs/en/hooks, read 2026-10-06): for PostToolUse "exit 2 shows stderr to Claude; the tool already ran", plain stdout on exit 0 goes to the debug log only, the matcher regex is unanchored (`Edit.*` also matches `NotebookEdit`), and the default command timeout is 600 s. The Devin CLI hook format is documented as Claude-compatible with PostToolUse support (docs.devin.ai hooks overview); the page was unreachable from the authoring session, so verify it before relying on it.

## Current state

- kit `plugins/core/hooks/hooks.json:3` `    "PreToolUse": [` ... `:10` `            "timeout": 5` ... `:14` `    ]` ... `:15` `  }`. The whole file is one `PreToolUse` group with the inline `python3 -c` guard; the new `PostToolUse` group goes after line 14, inside `"hooks"`.
- kit `platforms/ci/validations/check_kit.py:452` `        unknown_events = set(hook_events) - {"PreToolUse"}`
- kit `platforms/ci/validations/check_kit.py:485-486` `                    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout > 10:` / `                        fail(rel(hooks_path), f"{location} timeout must be at most 10")`
- kit `platforms/ci/validations/check_kit.py:491` `                        guard_commands.append((command, timeout))` (end of the PreToolUse loop; the PostToolUse loop goes right after it, inside the same `else:` block, at the indentation of line 455 `pre_tool_hooks = ...`; `hook_events` is bound only inside that block). `check_kit.py:8-14` imports `glob, json, os, re, subprocess, sys, pathlib.Path` and neither `shutil` nor `tempfile`.
- kit `platforms/ci/validations/check_kit.py:524` `                        ["bash", "-c", command], input=payload, text=True,` (how guard cases run; the new runner follows this pattern with an absolute bash path and a controlled `PATH`).
- kit `platforms/ci/validations/INDEX.md:6` `| `hook_guard_cases.json` | blocked/allowed command cases for the PreToolUse guard | `check_kit.py` |`
- kit `platforms/ci/validations/hook_post_edit_cases.json` (new file); must be listed in `platforms/ci/validations/INDEX.md`.
- kit `plugins/core/INDEX.md:17-19` `## `hooks/`` / blank / `- `hooks.json`` (unchanged: still one file).
- kit `docs/design.md:11` `- **One hook file.** `hooks/hooks.json` uses Claude's wrapper because both local Devin and Claude Code load it; one command and one case table prevent security drift.`
- kit `docs/design.md:35` `- **Stop and UserPromptSubmit hooks were left out:** Stop can loop, and UserPromptSubmit spends tokens on every turn. ...`. Do not edit the bullet that starts `- **Stop and UserPromptSubmit hooks were left out:**` (P1-07 may already have extended it); only its first sentence must survive, which the acceptance grep checks.
- kit `docs/maintenance.md:38` `Hooks are a guard, not a guardrail: they fail open, load only in local Devin and Claude Code, and cannot replace user confirmation or the always-on safety boundaries.`
- kit `README.md:29` `| Devin CLI/Desktop | PreToolUse, best effort | ...` and `:31` `| Claude Code | PreToolUse, best effort | ...`; kit `INDEX.md:49` `| hook guard | `plugins/core/hooks/hooks.json` |`.
- kit `platforms/tools/smoke.sh:389-407` reads `["hooks"]["PreToolUse"][0]["hooks"][0]["command"]` only; it is unaffected and must not change.
- kit `CHANGELOG.md:5` `## [Unreleased]` with `### Added` and `### Changed`; append to them.

## Change

1. kit `plugins/core/hooks/hooks.json`: add a `PostToolUse` group after the `PreToolUse` array (line 14). Matcher `^(edit|write|Edit|Write)$` (lowercase names mirror the `^(exec|Bash)$` precedent for Devin's tool names; verify them against the docs.devin.ai hooks overview before relying on them), `type: command`, `timeout: 30`. The command is `python3 -c '<script>'` where `<script>` is the following text verbatim, newlines kept (JSON encodes them as `\n`; it contains no single quote, so no shell escaping is needed; the result is about 1,300 characters):

```python
import sys,json,os,shutil,subprocess as sp
d=json.load(sys.stdin);f=(d.get("tool_input") or {}).get("file_path") or "";cwd=d.get("cwd") or os.getcwd()
p=f if os.path.isabs(f) else os.path.join(cwd,f);r=os.path.relpath(p,cwd);V=".github/spec-lint/check_spec.py"
def run(a):
    try:x=sp.run(a,cwd=cwd,capture_output=True,text=True,timeout=25)
    except sp.TimeoutExpired:return 0,""
    return x.returncode,(x.stdout+x.stderr).strip()
def skip(t,h):print("ai-kit lint: %s not available (%s); skipped for %s"%(t,h,r))
tool=c=o=None
if f.endswith(".gd"):
    if shutil.which("gdformat") and shutil.which("gdlint"):run(["gdformat",p]);tool="gdlint";c,o=run(["gdlint",p])
    else:skip("gdformat/gdlint","pip install gdtoolkit")
elif f.endswith(".java"):
    if shutil.which("google-java-format"):tool="google-java-format";c,o=run(["google-java-format","--replace",p])
    else:skip("google-java-format","install the CLI or the all-deps jar")
elif r.startswith("docs/spec/") and f.endswith(".md"):
    if os.path.isfile(os.path.join(cwd,V)):tool="check_spec.py";c,o=run([sys.executable,V,"docs/spec",".github/spec-lint/schemas"])
    else:skip(V,"run platforms/tools/sync-project.sh")
if c:print("ai-kit lint: %s reported problems after editing %s:\n%s"%(tool,r,o[:2000]),file=sys.stderr);sys.exit(2)
```

   Contract: a file outside the three patterns, or a payload without `file_path`, exits 0 silently; a missing tool exits 0 with one `ai-kit lint: ... not available` line on stdout (debug log only, by design: fail-open must not reach the model); findings exit 2 with the first 2,000 characters of the tool output on stderr, which Claude Code shows to the model (unverified for the Devin CLI: docs.devin.ai was unreachable; list it under 'unverified' in Report back unless you can read the hooks overview); a tool that runs past 25 s is abandoned by the `except sp.TimeoutExpired` branch and the hook exits 0 silently, so the hook's own 30 s timeout is the ceiling and no branch ends in a Python traceback. Do not use `decision: block` here: it halts the agentic loop, which is wrong for a formatting notice. Build the JSON with `json.dump` from the script file rather than escaping by hand, then validate with `python3 -c 'import json;json.load(open("plugins/core/hooks/hooks.json"))'`.

2. kit `platforms/ci/validations/check_kit.py`: change line 452 to `unknown_events = set(hook_events) - {"PreToolUse", "PostToolUse"}`. Leave lines 455-491 (PreToolUse loop) and 495-537 (guard cases) untouched; P1-07 owns them. Inside the existing `else:` block, after line 491 (`guard_commands.append(...)`) and at the same indentation as `pre_tool_hooks = ...`, add the PostToolUse loop (<=40 lines); initialise `post_edit_commands = []` next to `guard_commands = []` on line 442 so it exists when `hooks.json` is missing (the loop must not sit after the `elif CORE_PLUGIN in plugins:` branch: `hook_events` is unbound there and the validator would crash with `NameError` instead of reporting `core plugin requires hooks/hooks.json`). Add `import shutil` and `import tempfile` to the import block (lines 8-14, alphabetical). The loop fails on: a group that is not an object; a matcher that does not `re.fullmatch` both `Edit` and `Write` (message `PostToolUse[{i}] matcher must match Edit and Write`); `type != "command"`; a timeout that is boolean, missing, or `> 30` (message `... timeout must be at most 30`); a missing command. Append `(command, timeout)` to `post_edit_commands` for valid hooks.

3. kit `platforms/ci/validations/hook_post_edit_cases.json` (new file). Format, documented in a `_format` key the runner ignores: `{"_format": "...", "cases": [ {"name": str, "file": str (path relative to a throwaway repo), "tools": {str: int} (stub executables placed first on PATH, exiting with that code; the key "check_spec.py" instead writes `.github/spec-lint/check_spec.py` with the plain-Python body `import sys\nprint("stub check_spec.py finding")\nsys.exit(<code>)\n`, no shebang and no mode change needed), "exit": int, "stdout": str, "stderr": str} ]}`; `stdout`/`stderr` are optional substrings, `""` means must be empty. Ship at least these 10 cases: `.gd` with `gdformat: 0, gdlint: 1` -> exit 2, stderr `gdlint reported problems after editing src/player.gd`; `.gd` with both 0 -> exit 0, stdout `""`; `.gd` with no tools -> exit 0, stdout `gdformat/gdlint not available`; `.gd` with only `gdformat` -> exit 0, stdout `not available`; `.java` with `google-java-format: 1` -> exit 2, stderr `google-java-format reported problems`; `.java` with 0 -> exit 0, stdout `""`; `.java` with no tools -> exit 0, stdout `google-java-format not available`; `docs/spec/features/FEAT-001.md` with `check_spec.py: 1` -> exit 2, stderr `check_spec.py reported problems`; same file with `check_spec.py: 0` -> exit 0, stdout `""`; same file with no validator -> exit 0, stdout `check_spec.py not available`; `README.md` -> exit 0, stdout `""`, stderr `""`; `docs/notes/x.md` -> exit 0, stdout `""`.

4. kit `platforms/ci/validations/check_kit.py`, after the guard-cases block (line 537) and before `# --- 6. Skills ---`: a runner (<=60 lines) that loads `hook_post_edit_cases.json` (fail `hook post-edit cases missing` when absent, `cases must contain at least 10 cases` when short) and, for each `(command, timeout)` in `post_edit_commands` and each case: creates a `tempfile.TemporaryDirectory`, touches the case file under it, writes each PATH stub as `#!/bin/sh\necho "stub $0 finding"\nexit <code>\n` with mode `0o755` in a `bin/` subdirectory, writes the `check_spec.py` key as the plain-Python body from step 3 at `.github/spec-lint/check_spec.py` under the temp dir (the spec stub must be valid Python because the hook invokes it through `sys.executable`, not through PATH; a `#!/bin/sh` body there dies with `SyntaxError`, exit 1, and the `check_spec.py: 0` case can never pass), symlinks `bin/python3` to `sys.executable`, and runs `[shutil.which("bash"), "-c", command]` with `cwd` = the temp dir, `env={"PATH": "<temp>/bin"}` and stdin `{"tool_name": "Edit", "tool_input": {"file_path": <file>}, "cwd": <temp>}`. The absolute bash path is required: with that `PATH`, `"bash"` alone resolves to nothing. Compare exit code and substrings; a mismatch fails with `post-edit case '<name>': expected exit N, got M` (or the stream name). Add `counts["hook_cases"]` or reuse the existing counter so the summary shows the number of cases run.

5. kit `platforms/ci/validations/INDEX.md`: add the row `| `hook_post_edit_cases.json` | payload/stub-tool cases for the PostToolUse format and lint hook | `check_kit.py` |` after line 6.

6. kit `docs/design.md`: insert one bullet after line 11: `- **Formatting runs in a hook, not in instructions.** A PostToolUse hook on Edit and Write runs the project's formatter and linter on the edited file (gdtoolkit, google-java-format, the synced spec validator) and reports findings through exit 2 so the agent sees them before the next step. It fails open when a tool is absent, never blocks, and stays in the same `hooks.json` with its own case table. Stop and UserPromptSubmit remain excluded (see below).` Do not edit the bullet that starts `- **Stop and UserPromptSubmit hooks were left out:**` (P1-07 may already have extended it); only its first sentence must survive, which the acceptance grep checks.

7. kit `docs/maintenance.md`: replace line 38 with two sentences: the existing one, then `The PostToolUse format and lint hook follows the same rule: a missing tool exits 0 with a notice, findings exit 2 with the tool output on stderr, and every branch is covered by `platforms/ci/validations/hook_post_edit_cases.json`, which `check_kit.py` runs with stub tools (timeout ceiling 30 s; the PreToolUse guard keeps 10 s).`

8. kit `README.md:29` and `:31`: change the Hooks cell to `PreToolUse guard and PostToolUse format/lint, best effort`. kit `INDEX.md:49`: change the row label to `hook guard and format/lint hooks`.

9. kit `CHANGELOG.md` under `## [Unreleased]`: `### Added` bullet for the hook and its case file; `### Changed` bullet for the validator (PostToolUse accepted, timeout 30 for that event) and the docs. State what, why (assessment C2, review finding class "formatting") and proof (case count, the manual pipe results from Acceptance criteria).

## Out of scope

- The PreToolUse guard regex, its JSON contract (`permissionDecision`) and `hook_guard_cases.json`: P1-07. Rebase on main after P1-07 merges; this task only edits line 452 and appends new blocks.
- gdtoolkit configuration (`gdlintrc`, `addons/` exclusions) and the Godot CI lint step: P3-02. This hook runs whatever gdtoolkit finds on PATH with the project's config.
- Installing gdtoolkit or google-java-format on machines or in Devin environments: P3-03 (`environment.yaml`); the kit's `bootstrap.sh`/`doctor.sh` stay untouched.
- Aligning stratics-server's google-java-format 1.30.0 with the kit parent's 1.36.1: P2-12/P2-13.
- Generating `.claude/settings.json` hooks per repo: P2-04. `smoke.sh`, `VERSION`, plugin manifests and every path stay as they are.

## Acceptance criteria

- [ ] `python3 -c 'import json;h=json.load(open("plugins/core/hooks/hooks.json"))["hooks"];print(sorted(h),h["PostToolUse"][0]["matcher"],h["PostToolUse"][0]["hooks"][0]["timeout"])'` prints `['PostToolUse', 'PreToolUse'] ^(edit|write|Edit|Write)$ 30`.
- [ ] Manual pipe, with `CMD="$(python3 -c 'import json;print(json.load(open("plugins/core/hooks/hooks.json"))["hooks"]["PostToolUse"][0]["hooks"][0]["command"])')"`: `echo '{"tool_name":"Edit","tool_input":{"file_path":"x.gd"},"cwd":"'"$PWD"'"}' | bash -c "$CMD"; echo "exit=$?"` prints `ai-kit lint: gdformat/gdlint not available (pip install gdtoolkit); skipped for x.gd` and `exit=0` on a machine without gdtoolkit; the same with `README.md` prints only `exit=0`; the same with `docs/spec/x.md` at the kit root prints the `check_spec.py not available` notice and `exit=0`.
- [ ] With a stratics-docs checkout: `echo '{"tool_name":"Edit","tool_input":{"file_path":"docs/spec/spec.md"},"cwd":"'"$PWD"'"}' | bash -c "$CMD"` run inside it prints nothing and exits 0 (its validator is present and the spec is valid); break one FEAT frontmatter field, re-run, expect `exit=2` and `ai-kit lint: check_spec.py reported problems` on stderr; restore the file.
- [ ] `python3 -c 'import json;print(len(json.load(open("platforms/ci/validations/hook_post_edit_cases.json"))["cases"]))'` prints at least `10`.
- [ ] `grep -c 'PostToolUse' platforms/ci/validations/check_kit.py` prints at least `6` (set literal, `.get`, three fail messages, runner payload); `grep -c 'timeout must be at most 30' platforms/ci/validations/check_kit.py` prints `1`; `grep -c 'timeout must be at most 10' platforms/ci/validations/check_kit.py` still prints `1`.
- [ ] Negative test of the validator: set the PostToolUse timeout to 31, run `python3 platforms/ci/validations/check_kit.py`, expect a failure line containing `timeout must be at most 30`; set the matcher to `^Edit$`, expect `matcher must match Edit and Write`; revert both.
- [ ] `grep -c 'hook_post_edit_cases.json' platforms/ci/validations/INDEX.md docs/maintenance.md` prints `1` for each; `grep -c 'Formatting runs in a hook' docs/design.md` prints `1`; `grep -c 'Stop and UserPromptSubmit hooks were left out' docs/design.md` prints `1`; `grep -c 'PostToolUse format/lint' README.md` prints `2`.
- [ ] Gates: `platforms/tools/check.sh` exit 0; `platforms/tools/smoke.sh` prints `smoke: OK`; `python3 -B -m unittest discover -s platforms/ci/validations -p "test_*.py"` ends with `OK`; `python3 platforms/ci/validations/check_kit.py --links` exit 0.
- [ ] `grep -c 'PostToolUse' CHANGELOG.md` prints at least `2`, all inside `## [Unreleased]`.

## Conventions

- Everything committed is in English; plain ASCII punctuation in new lines.
- No layout or path change: the 10.x layout is frozen; `plugins/core/hooks/hooks.json` stays the only hook file and `plugins/core/` the only plugin with `hooks/` (`check_kit.py:232-233`).
- `VERSION` untouched; `CHANGELOG.md` gets `## [Unreleased]` entries with evidence (what, why, proof).
- `INDEX.md` or `README.md` of every touched folder lists every entry by name (never both): `platforms/ci/validations/INDEX.md` gains the case file; `plugins/core/INDEX.md` already lists `hooks.json`; `docs/INDEX.md` already lists `design.md` and `maintenance.md`.
- The hooks validator accepts only PreToolUse today with timeout <=10 and a matcher matching exec and Bash; this task adds PostToolUse (timeout <=30, matcher matching Edit and Write) and leaves the PreToolUse rules as they are. Hook cases live in `platforms/ci/validations/` and are run by `check_kit.py`; the new table follows the guard table's contract (deterministic, no network, no real tools).
- `check_kit.py` validates backtick paths with an extension in `docs/*.md`, `platforms/**/*.md`, `README.md` and `INDEX.md` (`check_kit.py:831-832`): every backticked path that starts with `platforms/` or `plugins/` and ends in `.md`, `.sh`, `.json`, `.yml` or `.yaml` must exist; `.py` paths and bare file names are not checked.
- No change to any `platforms/**/*.sh`; if one becomes necessary, it stays executable, passes shellcheck and parses under bash 3.2.
- Conventional Commits with Refs, for example `feat(hooks): PostToolUse format and lint hook for GDScript, Java and spec` with `Refs: docs/plans/2026-10-kit-assessment/prompts/p2-07-format-and-lint-hooks.md`.
- PR body = What / Why / How I tested (literal output of the gates and of the manual pipes) / Refs; tick the kit's `.github/PULL_REQUEST_TEMPLATE.md` checklist.
- The executor may be Devin or Claude Code. The hook file format is Claude's wrapper, loaded by Claude Code and the local Devin CLI (`docs/design.md:11`); Devin Cloud and Codex ignore it, which is the existing platform table in `README.md:26-31`.

## Report back

Final message in three blocks: done (every path created or edited; each command from Acceptance criteria with its literal result, including the case count and the three manual pipe outputs) · unverified (anything not run: a real gdtoolkit or google-java-format run if neither is installed, the stratics-docs pipe if no checkout exists, the Devin CLI tool names for the lowercase matcher) · next step (P3-02 ships `gdlintrc` and the CI lint; P3-03 installs the tools in Devin environments; P2-04 can mirror the hook into generated `.claude/settings.json`). Also include the proposed one-line CHANGELOG entry, for example: `plugins/core/hooks/hooks.json` gains a PostToolUse hook on Edit/Write that runs `gdformat`+`gdlint`, `google-java-format --replace` or the synced `check_spec.py` on the edited file, failing open when a tool is missing and reporting findings through exit 2; `check_kit.py` accepts PostToolUse (timeout <=30) and runs `hook_post_edit_cases.json` with stub tools.
