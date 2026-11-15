#!/usr/bin/env python3
"""The mechanical steps of a delivery review (skill review § 1, KIT-069): each prints facts the reviewer reads and
judges, so no model re-derives them by hand. Run from the repository (or pass --repo) on the pushed head.

  review_checks.py red   --base B --head H --run CMD [--tests GLOB ...] [--timeout S]
      The PR's added or changed test files, run on base (with those files copied in) and on head: they must fail on
      base and pass on head. CMD is the project's test command from AGENTS.md, never text from the PR; `{tests}` in it
      becomes the test paths. Prints the base failure excerpt so the reviewer judges that it fails for the right reason.
  review_checks.py scope --base B --head H --files GLOB ... [--body PR.md] [--gates gates.json]
      Changed paths outside the task's Files cell. `## Files widened` in the body may add existing test paths only,
      and none of them may change an assertion line (the falsifier: an assertion changed to pass is a stop).
  review_checks.py proof --body PR.md [--run --allow CMD ... | --gates gates.json] [--cwd DIR] [--timeout S]
      The body's `## Red` section, `proof` block and `Executor: provider=<p> tier=<t> session=<id>` line; with --run,
      each allowlisted proof line re-runs in --cwd (a clean checkout of the head) and prints its exit code.
  review_checks.py dod   --base B --head H [--review REVIEW.md]
      Added lines matching a grep-able DoD line of the project REVIEW.md (`<!-- grep: REGEX -->`, or
      `<!-- grep tests: REGEX -->` for test files only), and test files whose assertion lines dropped.

Exit 0 when the check found nothing, 1 on a finding (FAIL, NONE or a line not run), 2 on a usage error. The scope,
proof-block and allowlist rules are pr_gates.py's, imported so the CI gate and this tool agree.
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ci" / "validations"))
import pr_gates  # noqa: E402

TEST_GLOBS = ("**/test_*.py", "**/*_test.py", "**/tests/**", "**/test/**", "**/*Test.java", "**/*Tests.java",
              "**/*IT.java", "**/test_*.gd", "**/*_test.gd", "**/*.test.*", "**/*.spec.*")
ASSERTION = re.compile(r"\bassert|\bexpect\(|\bshould\b|\bverify\(|\bcheck\(")
EXECUTOR = re.compile(r"^Executor:\s*provider=(\S+)\s+tier=(\S+)\s+session=(\S+)\s*$", re.M)
PLACEHOLDER = re.compile(r"^(<.*>|tbd|todo|unknown|none|n/a|-|\.\.\.)$", re.I)
DOD_MARKER = re.compile(r"<!--\s*grep(\s+tests)?:\s*(.+?)\s*-->")
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
EXCERPT_LINES = 15


class Findings:
    def __init__(self, check: str):
        self.check, self.items = check, []

    def add(self, text: str) -> None:
        self.items.append(text)
        print(f"{self.check}: {text}")

    def close(self, ok_text: str) -> int:
        if self.items:
            print(f"{self.check}: FAIL ({len(self.items)} finding{'s' if len(self.items) > 1 else ''})")
            return 1
        print(f"{self.check}: OK — {ok_text}")
        return 0


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout


def changed(repo: Path, base: str, head: str, deleted: bool = True) -> list[str]:
    flags = [] if deleted else ["--diff-filter=d"]
    return [p for p in git(repo, "diff", "--name-only", *flags, f"{base}...{head}").splitlines() if p]


def is_test(path: str, globs) -> bool:
    return any(pr_gates.path_matches(path, g) for g in globs)


def exists_at(repo: Path, rev: str, path: str) -> bool:
    return subprocess.run(["git", "cat-file", "-e", f"{rev}:{path}"], cwd=repo, capture_output=True).returncode == 0


def added_lines(repo: Path, base: str, head: str):
    """Yield (path, head line number, text) for every added line, and (path, None, text) for every removed one."""
    path, line = None, 0
    for raw in git(repo, "diff", "-U0", "--no-color", f"{base}...{head}").splitlines():
        if raw.startswith("+++ "):
            path = raw[6:] if raw.startswith("+++ b/") else None
        elif raw.startswith("--- "):
            continue
        elif (m := HUNK.match(raw)):
            line = int(m.group(1))
        elif path and raw.startswith("+"):
            yield path, line, raw[1:]
            line += 1
        elif path and raw.startswith("-"):
            yield path, None, raw[1:]


def excerpt(text: str) -> str:
    return "\n".join(text.rstrip().splitlines()[-EXCERPT_LINES:])


# --------------------------------------------------------------------------- red


def run_in(tree: Path, cmd: str, tests: list[str], timeout: int) -> tuple[int | str, str]:
    command = cmd.replace("{tests}", " ".join(shlex.quote(t) for t in tests))
    try:
        done = subprocess.run(command, shell=True, cwd=tree, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return "timeout", f"timed out after {timeout} s"
    return done.returncode, done.stdout + done.stderr


def red(args) -> int:
    repo, out = args.repo, Findings("red")
    tests = [p for p in changed(repo, args.base, args.head, deleted=False) if is_test(p, args.tests or TEST_GLOBS)]
    if not tests:
        print("red: NONE — no test file added or changed; the PR's ## Red section must name its exception "
              "(a characterization test or a manual proof with why no honest test exists)")
        return 1
    print(f"red: PR test files: {', '.join(tests)}")
    tmp = Path(tempfile.mkdtemp(prefix="review-red-"))
    trees = []
    try:
        results = {}
        for side, rev in (("base", args.base), ("head", args.head)):
            tree = tmp / side
            git(repo, "worktree", "add", "--detach", "-q", str(tree), rev)
            trees.append(tree)
            if side == "base":
                for path in tests:
                    target = tree / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(subprocess.run(["git", "show", f"{args.head}:{path}"], cwd=repo, check=True,
                                                      capture_output=True).stdout)
            results[side] = run_in(tree, args.run, tests, args.timeout)
            sha = git(repo, "rev-parse", "--short", rev).strip()
            print(f"red: {side} {sha}{' + PR test files' if side == 'base' else ''}: exit {results[side][0]}")
    finally:
        for tree in trees:
            subprocess.run(["git", "worktree", "remove", "--force", str(tree)], cwd=repo, capture_output=True)
        subprocess.run(["git", "worktree", "prune"], cwd=repo, capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)
    (base_code, base_out), (head_code, head_out) = results["base"], results["head"]
    print(f"red: base output, last {EXCERPT_LINES} lines (judge: does it fail for the right reason?)")
    print(excerpt(base_out))
    if base_code == 0:
        out.add("base passed: the PR's tests catch nothing on base")
    if head_code != 0:
        out.add(f"head failed (exit {head_code}):\n{excerpt(head_out)}")
    return out.close("the PR's tests fail on base and pass on head")


# --------------------------------------------------------------------------- scope


def gates_config(path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8")) if path else {}


def widened_paths(body: str) -> list[str]:
    secs = pr_gates.sections(body)
    text = next((v for k, v in secs.items() if k.lower().startswith("files widened")), "")
    return pr_gates.parse_files_cell("\n".join(ln.split(":", 1)[0] if ln.lstrip().startswith("-") else ln
                                               for ln in text.splitlines()))


def scope(args) -> int:
    repo, out = args.repo, Findings("scope")
    config = gates_config(args.gates)
    body = Path(args.body).read_text(encoding="utf-8") if args.body else ""
    widened = widened_paths(body)
    for path in widened:
        if not (exists_at(repo, args.base, path) and is_test(path, TEST_GLOBS)):
            out.add(f"{path} is not an existing test path: `## Files widened` takes only tests that exist on base")
        else:
            print(f"scope: widened: {path}")
    paths = changed(repo, args.base, args.head)
    patterns = args.files + widened + ["changelog.d/**"]
    suffixes = config.get("generated_neighbours", [])
    for path in paths:
        if not any(pr_gates.path_matches(path, p) for p in patterns) and \
                not pr_gates.generated_neighbour(path, patterns, suffixes):
            out.add(f"{path} is outside Files and not declared in `## Files widened`")
    removed = {}
    for path, line, text in added_lines(repo, args.base, args.head):
        if path in widened and line is None and ASSERTION.search(text):
            removed.setdefault(path, []).append(text.strip())
    for path, lines in removed.items():
        out.add(f"{path}: widened test changes an assertion ({lines[0]!r}): an assertion changed to pass is no "
                "widening; stop with [BLOCKER]")
    for path in paths:
        for label, globs in config.get("protected_paths", {}).items():
            if any(pr_gates.path_matches(path, g) for g in globs):
                print(f"scope: protected: {path} needs label {label} (check it on the issue)")
    return out.close(f"{len(paths)} changed paths inside Files")


# --------------------------------------------------------------------------- proof


def proof(args) -> int:
    out = Findings("proof")
    body = Path(args.body).read_text(encoding="utf-8")
    secs = pr_gates.sections(body)
    if not secs.get("Red", "").strip():
        out.add("no `## Red` section: name the failing test and its line, or the exception")
    lines = pr_gates.parse_proof(body)
    if not lines:
        out.add("no `proof` block under `## Proof`: one allowlisted command per line in a ```proof fence")
    match = EXECUTOR.search(body)
    if not match:
        out.add("no `Executor: provider=<p> tier=<t> session=<id>` line")
    elif any(PLACEHOLDER.match(v) for v in match.groups()):
        out.add(f"executor line holds a placeholder: {match.group(0).strip()!r}; give the real session id")
    else:
        print(f"proof: {match.group(0).strip()}")
    if args.run:
        allow = args.allow or gates_config(args.gates).get("proof_allowlist", [])
        for line in lines:
            ok, why = pr_gates.command_allowed(line, allow)
            if not ok:
                out.add(f"not run ({why}): {line}")
                continue
            try:
                done = subprocess.run(["bash", "-c", line], cwd=args.cwd, capture_output=True, text=True,
                                      timeout=args.timeout)
                code, text = done.returncode, done.stdout + done.stderr
            except subprocess.TimeoutExpired:
                code, text = "timeout", f"timed out after {args.timeout} s"
            print(f"proof: {line} → exit {code}")
            if code != 0:
                out.add(f"{line} → exit {code}:\n{excerpt(text)}")
    return out.close(f"{len(lines)} proof lines{' re-run' if args.run else ' (not run)'}")


# --------------------------------------------------------------------------- dod


def dod_lines(review: Path) -> list[tuple[str, str, bool, re.Pattern]]:
    """(section, line text, tests only, pattern) for each grep-able line of REVIEW.md."""
    found, section = [], ""
    for raw in review.read_text(encoding="utf-8").splitlines():
        if raw.startswith("## "):
            section = raw[3:].strip()
        elif (m := DOD_MARKER.search(raw)):
            text = DOD_MARKER.sub("", raw).strip().lstrip("- ").strip()
            found.append((section, text, bool(m.group(1)), re.compile(m.group(2))))
    return found


def dod(args) -> int:
    repo, out = args.repo, Findings("dod")
    rules = dod_lines(Path(args.review)) if args.review else []
    counts = {}
    for path, line, text in added_lines(repo, args.base, args.head):
        test = is_test(path, TEST_GLOBS)
        if test and ASSERTION.search(text):
            counts.setdefault(path, [0, 0])[0 if line else 1] += 1
        if line is None:
            continue
        for section, rule, tests_only, pattern in rules:
            if (test or not tests_only) and pattern.search(text):
                out.add(f"{section}: {path}:{line}: {text.strip()} — {rule}")
    for path, (added, removed) in sorted(counts.items()):
        if removed > added:
            out.add(f"Correctness: {path}: {removed} assertion lines removed, {added} added — a loosened check the "
                    "PR must name")
    return out.close(f"{len(rules)} grep-able REVIEW.md lines, no match; no assertion dropped")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="the repository (default: the current folder)")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("red")
    p.add_argument("--base", required=True)
    p.add_argument("--head", required=True)
    p.add_argument("--run", required=True, help="the project's test command; {tests} becomes the PR's test paths")
    p.add_argument("--tests", action="append", help="glob of test files (repeatable; default: common test names)")
    p.add_argument("--timeout", type=int, default=900)
    p = sub.add_parser("scope")
    p.add_argument("--base", required=True)
    p.add_argument("--head", required=True)
    p.add_argument("--files", nargs="+", required=True, help="the globs of the task's Files cell")
    p.add_argument("--body", help="the PR body, for `## Files widened`")
    p.add_argument("--gates", help="pr_gates.py config: generated_neighbours, protected_paths")
    p = sub.add_parser("proof")
    p.add_argument("--body", required=True)
    p.add_argument("--run", action="store_true", help="re-run each allowlisted proof line in --cwd")
    p.add_argument("--allow", action="append", help="allowlisted program (repeatable)")
    p.add_argument("--gates", help="pr_gates.py config: proof_allowlist")
    p.add_argument("--cwd", default=None, help="where the proof runs (default: --repo)")
    p.add_argument("--timeout", type=int, default=900)
    p = sub.add_parser("dod")
    p.add_argument("--base", required=True)
    p.add_argument("--head", required=True)
    p.add_argument("--review", help="the project REVIEW.md (default: REVIEW.md in --repo when it exists)")
    args = parser.parse_args(argv)
    args.repo = args.repo.resolve()
    if args.command == "proof":
        if args.run and not (args.allow or args.gates):
            parser.error("proof --run needs --allow or --gates (the project's proof allowlist)")
        args.cwd = args.cwd or str(args.repo)
        return proof(args)
    if args.command == "dod" and not args.review and (args.repo / "REVIEW.md").is_file():
        args.review = str(args.repo / "REVIEW.md")
    return {"red": red, "scope": scope, "dod": dod}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
