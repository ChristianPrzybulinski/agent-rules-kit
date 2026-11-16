#!/usr/bin/env python3
"""The red job of the kit's ci.yml (KIT-077): on a pull request it runs `review_checks.py red` on the merge commit
GitHub checks out, the base HEAD^1 against the PR head HEAD^2, with the kit's runner on the PR's test files, writes
the output to the job summary for the reviewer, and turns the verdict into the job's result:

  OK or EXEMPT (red exit 0)                   pass
  FLAG (exit 3): the reviewer judges it       pass, with a warning annotation
  NONE (exit 1: no test file changed)         pass, with a notice, when the PR body's `## Red` section opens with
                                              "Exception" (the form the PR template asks for); otherwise fail
  any other finding (exit 1) or error (2)     fail

On a push or a dispatch there is no pull request to compare, so the job says so and passes. The PR body is untrusted
text: it is read from the event file only to find that section's first line, and the reviewer judges the exception.

Usage: ci_red.py   (reads GITHUB_EVENT_NAME, GITHUB_EVENT_PATH, GITHUB_STEP_SUMMARY and GITHUB_WORKSPACE)
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
REVIEW_CHECKS = KIT / "platforms" / "tools" / "review_checks.py"
RUNNER = KIT / "platforms" / "tools" / "run_tests.py"
TESTS = "platforms/ci/validations"
SECTION = re.compile(r"^##\s+(.+?)\s*$")


def red_exception(body: str | None) -> str | None:
    """The first non-empty line of the body's `## Red` section when it opens with "Exception", else None."""
    lines = (body or "").replace("\r\n", "\n").split("\n")
    for index, line in enumerate(lines):
        heading = SECTION.match(line)
        if not heading or heading.group(1) != "Red":
            continue
        for text in lines[index + 1:]:
            if SECTION.match(text):
                return None
            if text.strip():
                return text.strip() if text.strip().startswith("Exception") else None
    return None


def verdict(code: int, output: str, body: str | None) -> tuple[int, str]:
    """(job exit code, annotation line) for red's exit code and output."""
    if code == 0:
        return 0, ""
    if code == 3:
        return 0, "::warning title=red::red flags what the reviewer must judge; read this job's summary"
    if code == 1 and "red: NONE" in output:
        exception = red_exception(body)
        if exception:
            return 0, ("::notice title=red::no test file changed; the PR's ## Red names an exception, which the "
                       f"reviewer judges: {exception[:200]}")
        return 1, ("::error title=red::no test file changed and the PR's ## Red names no exception (a line that "
                   "opens with \"Exception\")")
    return 1, f"::error title=red::red exited {code}; read this job's log"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=KIT, capture_output=True, text=True, check=True).stdout.strip()


def main() -> int:
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    if event != "pull_request":
        print(f"red: no pull request on a {event or 'local'} run; nothing to compare")
        return 0
    payload = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    body = (payload.get("pull_request") or {}).get("body")
    parents = git("rev-list", "--parents", "-n", "1", "HEAD").split()[1:]
    if len(parents) != 2:
        print("::error title=red::HEAD is not the pull request's merge commit (checkout with fetch-depth: 0)")
        return 1
    base, head = parents
    # the head's runner on each side's test folder; the tests and the code they import come from that side
    command = f"python3 -B {shlex.quote(str(RUNNER))} --start {TESTS} {{tests}}"
    result = subprocess.run([sys.executable, "-B", str(REVIEW_CHECKS), "red", "--base", base, "--head", head,
                             "--tests", f"{TESTS}/test_*.py", "--run", command, "--timeout", "1200"],
                            cwd=KIT, capture_output=True, text=True, errors="replace")
    output = result.stdout + result.stderr
    print(output, end="")
    code, annotation = verdict(result.returncode, output, body)
    if annotation:
        print(annotation)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(f"## red: base {base[:7]}, head {head[:7]}, exit {result.returncode}\n\n```text\n"
                         f"{output.replace('```', '` ` `')}\n```\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
