#!/usr/bin/env python3
"""Advisory complexity of changed Java and GDScript functions (KIT-031).

Usage: complexity.py [--base REF] [--jacoco XML]... [--threshold N] [FILE...]

Java: per method of a JaCoCo XML report the build already produced, CC = COMPLEXITY missed + covered,
coverage = INSTRUCTION covered / total and CRAP = CC^2 * (1 - coverage)^3 + CC; reports CRAP >= 10.
GDScript: runs `gdradon cc` (gdtoolkit) and reports CC > 10. gdradon line numbers do not match the source,
so its results join the source's own `func` spans by name. A function whose coverage is known scores CRAP and
any other scores CC, so GDScript coverage (KIT-034) only has to fill `Function.coverage`.

Without FILE the measured functions are those whose lines changed in `git diff -U0 <base>...HEAD`; with FILE
every function in those files is measured. stdout holds one `path function metric value` line per finding,
stderr the notices. Exit 0; with --threshold N, exit 1 when a reported value reaches N and exit 2 when a
JaCoCo report or gdradon that the change needs is missing. A bad ref exits 2.
"""
import argparse
import bisect
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

CRAP_LIMIT = 10.0  # Java target CRAP < 10 (code-standards § 3)
CC_LIMIT = 10  # GDScript target CC <= 10 (code-standards § 3)
REPORT_GLOBS = ("target/site/*/jacoco.xml", "*/target/site/*/jacoco.xml", "*/*/target/site/*/jacoco.xml")
GD_FUNC = re.compile(r"^(\s*)(?:static\s+)?func\s+([A-Za-z_]\w*)\s*\(")
GDRADON_LINE = re.compile(r"^\s+F \d+:\d+ (\S+) - [A-F] \((\d+)\)")
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
LAST_LINE = 10 ** 9


@dataclass
class Function:
    path: str
    name: str
    start: int
    end: int  # inclusive
    cc: int
    coverage: Optional[float] = None  # None: unknown, the function scores CC

    def score(self):
        if self.coverage is None:
            return "CC", float(self.cc)
        return "CRAP", self.cc ** 2 * (1 - self.coverage) ** 3 + self.cc

    def above_target(self):
        metric, value = self.score()
        return value >= CRAP_LIMIT if metric == "CRAP" else value > CC_LIMIT

    def line(self):
        metric, value = self.score()
        return f"{self.path} {self.name} {metric} {value:.1f}" if metric == "CRAP" else f"{self.path} {self.name} CC {self.cc}"


def notice(text):
    print(f"complexity: {text}", file=sys.stderr)


def git(*args):
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if result.returncode:
        notice(f"git {args[0]} failed: {result.stderr.strip()}")
        sys.exit(2)
    return result.stdout


def changed_lines(base):
    """{path: new-side line numbers} of the .java and .gd files changed in base...HEAD."""
    out = git("diff", "-U0", "--no-color", "--no-ext-diff", "--src-prefix=a/", "--dst-prefix=b/",
              f"{base}...HEAD", "--", "*.java", "*.gd")
    changes, path = {}, None
    for text in out.splitlines():
        if text.startswith("+++ "):
            path = None if text == "+++ /dev/null" else text[len("+++ b/"):]
            if path:
                changes.setdefault(path, set())
        elif path and (match := HUNK.match(text)):
            start, count = int(match.group(1)), int(match.group(2) or 1)
            changes[path].update(range(start, start + count) if count else {max(start, 1)})
    return changes


def touched(function, lines):
    return lines is None or any(function.start <= n <= function.end for n in lines)


def java_functions(reports, wanted):
    """Functions of the JaCoCo reports in the wanted {path: lines or None (whole file)}."""
    by_key = {}
    for report in reports:
        for package in ET.parse(report).getroot().iter("package"):
            for cls in package.iter("class"):
                key = "/".join(filter(None, (package.get("name"), cls.get("sourcefilename"))))
                simple = cls.get("name").rsplit("/", 1)[-1]
                by_key.setdefault(key, [])  # a class with no method (an interface) is in the report all the same
                for method in cls.iter("method"):
                    if method.get("line") is None:
                        continue
                    counts = {c.get("type"): (int(c.get("missed")), int(c.get("covered"))) for c in method.iter("counter")}
                    missed, covered = counts.get("INSTRUCTION", (0, 0))
                    coverage = covered / (missed + covered) if missed + covered else None
                    cc = sum(counts.get("COMPLEXITY", (0, 0)))
                    by_key[key].append(
                        Function("", f"{simple}.{method.get('name')}", int(method.get("line")), LAST_LINE, cc, coverage))
    newest = max(os.path.getmtime(r) for r in reports)
    found = []
    for path, lines in wanted.items():
        key = next((k for k in by_key if path == k or path.endswith("/" + k)), None)
        if key is None:
            notice(f"{path} is not in the JaCoCo report; CRAP not computed")
            continue
        if os.path.getmtime(path) > newest:
            notice(f"{path} is newer than the JaCoCo report; its numbers may be stale")
        # A lambda (name with `$`) shares the span of the method that encloses it.
        starts = sorted({f.start for f in by_key[key] if "$" not in f.name.rsplit(".", 1)[-1]})
        for function in by_key[key]:
            index = bisect.bisect_right(starts, function.start)
            function.path = path
            function.start = starts[index - 1] if index else function.start
            function.end = starts[index] - 1 if index < len(starts) else LAST_LINE
            if touched(function, lines):
                found.append(function)
    return found


def gd_spans(path):
    """(name, first line, last line) of every `func` in a .gd file, by indentation."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    spans = []
    for number, text in enumerate(lines, 1):
        match = GD_FUNC.match(text)
        if not match:
            continue
        indent, end = len(match.group(1).expandtabs(4)), number
        for later in range(number + 1, len(lines) + 1):
            body = lines[later - 1].expandtabs(4)
            stripped = body.strip()
            outdented = len(body) - len(body.lstrip()) <= indent
            if not stripped or (outdented and stripped.startswith("#")):
                continue
            if outdented and not stripped.startswith(")"):
                break  # a statement back at the `func` indentation ends the body
            end = later
        spans.append((match.group(2), number, end))
    return spans


def gdradon_cc(paths):
    """{normalized path: {name: highest CC}} from `gdradon cc`, or None when gdradon is not on PATH."""
    if not shutil.which("gdradon"):
        return None
    result = subprocess.run(["gdradon", "cc", *paths], capture_output=True, text=True, check=False)
    ccs, current = {}, None
    for text in result.stdout.splitlines():
        if text and not text[0].isspace():
            current = ccs.setdefault(os.path.normpath(text.strip()), {})
        elif current is not None and (match := GDRADON_LINE.match(text)):
            current[match.group(1)] = max(current.get(match.group(1), 0), int(match.group(2)))
    for error in (result.stderr.strip().splitlines() or [])[:3]:
        notice(f"gdradon: {error}")
    return ccs


def gd_functions(wanted, ccs):
    found = []
    for path, lines in wanted.items():
        by_name = ccs.get(os.path.normpath(path), {})
        for name, start, end in gd_spans(path):
            function = Function(path, name, start, end, by_name.get(name, 0))
            if name in by_name and touched(function, lines):
                found.append(function)
    return found


def main():
    ap = argparse.ArgumentParser(description="Advisory complexity of changed Java and GDScript functions")
    ap.add_argument("files", nargs="*", help="measure every function in these files instead of the changed ones")
    ap.add_argument("--base", default="origin/main", help="ref the change is compared against (default origin/main)")
    ap.add_argument("--jacoco", action="append", default=[],
                    help="JaCoCo XML report (default: target/site/*/jacoco.xml up to two directories down)")
    ap.add_argument("--threshold", type=float, help="exit 1 when a reported value reaches N")
    args = ap.parse_args()
    reports = [Path(p).resolve() for p in args.jacoco]
    if args.files:
        wanted = {p: None for p in args.files}
    else:
        os.chdir(git("rev-parse", "--show-toplevel").strip())
        wanted = changed_lines(args.base)
    java = {p: n for p, n in wanted.items() if p.endswith(".java") and "/src/test/" not in f"/{p}"}
    gd = {p: n for p, n in wanted.items() if p.endswith(".gd") and Path(p).is_file()}
    functions, missing = [], False
    if java:
        reports = reports or sorted({p.resolve() for g in REPORT_GLOBS for p in Path(".").glob(g)})
        absent = [str(r) for r in reports if not r.is_file()]
        if not reports or absent:
            where = ", ".join(absent) or "target/site/*/jacoco.xml"
            notice(f"no JaCoCo report at {where}; CRAP not computed for {len(java)} changed Java file(s); "
                   "build the report first or pass --jacoco")
            missing = True
        else:
            functions += java_functions(reports, java)
    if gd:
        ccs = gdradon_cc(list(gd))
        if ccs is None:
            notice(f"gdradon not available (pip install gdtoolkit); skipped for {len(gd)} .gd file(s)")
            missing = True
        else:
            functions += gd_functions(gd, ccs)
    findings = sorted((f for f in functions if f.above_target()), key=lambda f: (-f.score()[1], f.path, f.name))
    for function in findings:
        print(function.line())
    notice(f"{len(findings)} of {len(functions)} measured function(s) above target "
           f"(Java CRAP < {CRAP_LIMIT:g}, GDScript CC <= {CC_LIMIT})")
    if args.threshold is None:
        return 0
    if missing:
        return 2
    return 1 if any(f.score()[1] >= args.threshold for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
