---
description: Always/never constraints for Python files; procedures stay in skills code-standards and testing.
trigger: glob
globs:
  - "**/*.py"
  - "**/pyproject.toml"
paths:
  - "**/*.py"
  - "**/pyproject.toml"
---

Always/never for `*.py` and `pyproject.toml`. Procedures: skill `code-standards` (tests: `testing`; untrusted input: `security`).

- Always: run the interpreter the repo names (`AGENTS.md`, `.python-version`, `requires-python`, a pinned path); on macOS a bare `python3` can be the Xcode 3.9, so read `python3 --version` before trusting a result.
- Always: the standard library first; a third-party import or a new `pyproject.toml` dependency is a dependency change (ask first) with its version pinned.
- Always: type hints on every new or changed signature (`def load(path: Path, *, strict: bool = False) -> dict[str, str]:`); `typing.Literal` for a fixed set of strings; a `dataclass` instead of a tuple of three or more fields.
- Always: `pathlib.Path` for paths and an explicit `encoding="utf-8"` on every text read and write.
- Always: `subprocess.run([...], check=True)`, or an explicit return-code check, with the arguments as a list; never `shell=True` with interpolated text or `os.system`.
- Never: a mutable default argument (`def f(items=[])`); default to `None` and build the value inside.
- Never: a bare `except:` or an `except Exception: pass`; catch the narrowest exception around the line that raises and chain with `raise NewError(...) from err`.
- Never: `assert` to validate runtime input (`python -O` strips it); raise `ValueError` or the module's own error.
- Never: `eval`, `exec`, `pickle.loads` or `yaml.load` without a safe loader on data from outside the repo; parse with `json` or `yaml.safe_load`, and run a script that reads downloaded files with `python3 -I`.
- Never: a bare `# noqa` or `# type: ignore` to hide a finding; name the code on the narrowest line (`# noqa: E402` after a `sys.path` insert) and fix the code when it can be fixed.
- Always: tests in the framework the repo already runs (`unittest` when there is no pytest configuration), and before "done" the literal tail of its test command and of the linter the repo configures.
