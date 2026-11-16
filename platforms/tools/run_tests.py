#!/usr/bin/env python3
"""The kit's test runner (KIT-077): selects the tests under platforms/ci/validations by layer, and the integration
tests by the files a change touches, then runs them in parallel worker processes. CI's jobs and `check.sh --tests`
call it; `python3 -B -m unittest <module>` still runs one module whole.

Usage: run_tests.py [--layer L[,L...]] [--changed-from REF] [--shard I/N] [--jobs N] [--durations N] [--json FILE]
                    [--list] [--start DIR] [FILE ...]

Each test module sets LAYER; a TestCase class, or one test method (`test_x.LAYER = "performance"` after it), may
set its own:
  unit         one function in-process: no subprocess, no git, milliseconds
  contract     the shape between parts, read in-process: workflows, schemas, frontmatter, manifests
  integration  parts together: a kit script run for real, a throwaway git repository
  functional   the kit synced into the fixture consumer project, whose own checks then run; the whole smoke.sh
  performance  latency budgets, run one at a time after the rest, so no other test loads the machine
An integration class lists COVERS, the globs of the files it exercises (pr_gates.py globs: `*` stays inside a folder,
`**` crosses them). With --changed-from REF it runs only when a file that differs between REF and the working tree
matches its COVERS or is its own test module, or when a changed file under platforms/ or plugins/ that is no Markdown
file and no test module matches no COVERS at all (unknown code runs the whole layer). Other layers ignore it.

--shard I/N runs the I-th of N interleaved slices of the selected chunks (a unit or contract class is one chunk, a
test of a slower layer one), so N CI jobs share a layer. FILE names test modules under --start (default this kit's
platforms/ci/validations) to run whole, whatever their layers and untagged ones too: the red job runs the PR's test
files on the base commit that way. The runner keeps its own helper out of the tests' imports, so a base run imports
only the base's modules. The summary keeps unittest's lines (`Ran N tests in`, `OK`, `FAILED (...)`) and each
failure's traceback, then the skips by reason; --durations N adds the slowest tests, --json FILE every test's layer,
seconds and outcome.

Exit 0 when every selected test passed or skipped, or when --changed-from leaves nothing to run; 1 on a failure or
an error; 2 on a usage error: an unknown layer, a test class with no layer or an unknown one, an integration class
without COVERS, a REF git cannot read, or nothing selected without --changed-from.
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import multiprocessing
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
TESTS = KIT / "platforms" / "ci" / "validations"
# The PR gates' glob rules, loaded under a private name: a test that imports pr_gates gets the copy beside it (on a
# base checkout, the base's), never this one.
_SPEC = importlib.util.spec_from_file_location("_run_tests_pr_gates", TESTS / "pr_gates.py")
pr_gates = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(pr_gates)

LAYERS = ("unit", "contract", "integration", "functional", "performance")
FAST = ("unit", "contract")  # a class of these layers runs as one chunk; any other test is a chunk of its own
SLOW = ("integration", "functional", "performance")
CODE = ("platforms/", "plugins/")
TEST_MODULE = "platforms/ci/validations/test_*.py"
SEPARATOR1, SEPARATOR2 = "=" * 70, "-" * 70


class Entry:
    """One discovered test: its id, layer, COVERS globs and module path relative to the kit."""

    def __init__(self, test, layer, covers, module):
        self.test, self.id, self.layer, self.covers, self.module = test, test.id(), layer, tuple(covers), module

    @property
    def cls(self):
        return self.id.rsplit(".", 1)[0]


def iter_tests(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from iter_tests(item)
        else:
            yield item


def discover(start=TESTS, files=()):
    """(entries, import failures, problems): every test with its layer, the loader's failed imports (run as errors)
    and one line per class with no layer, an unknown one or an integration class without COVERS. With files, only
    those modules, and an untagged class is no problem."""
    loader = unittest.TestLoader()
    if files:
        sys.path.insert(0, str(start))
        suite = unittest.TestSuite(loader.loadTestsFromName(Path(name).stem) for name in files)
    else:
        suite = loader.discover(str(start), pattern="test_*.py", top_level_dir=str(start))
    entries, failed, problems = [], [], {}
    for test in iter_tests(suite):
        cls = type(test)
        if cls.__module__.startswith("unittest."):
            failed.append(test)
            continue
        module = sys.modules[cls.__module__]
        method = getattr(test, getattr(test, "_testMethodName", ""), None)
        layer = getattr(method, "LAYER", None) or getattr(cls, "LAYER", None) or getattr(module, "LAYER", None)
        covers = getattr(cls, "COVERS", None) or getattr(module, "COVERS", None) or ()
        name = f"{cls.__module__}.{cls.__name__}"
        if files:
            pass
        elif layer not in LAYERS:
            problems[name] = f"{name}: LAYER {layer!r} is none of {', '.join(LAYERS)}"
        elif layer == "integration" and not covers:
            problems[name] = f"{name}: an integration class lists the files it exercises in COVERS"
        path = Path(module.__file__).resolve()
        rel = path.relative_to(KIT).as_posix() if KIT in path.parents else path.as_posix()
        entries.append(Entry(test, layer, covers, rel))
    return entries, failed, sorted(problems.values())


def matches(path, globs):
    return any(pr_gates.path_matches(path, glob) for glob in globs)


def unknown_code(changed, every_cover):
    """The changed files under platforms/ or plugins/ that no COVERS names: code no integration class claims."""
    return [p for p in changed if p.startswith(CODE) and not p.endswith(".md")
            and not pr_gates.path_matches(p, TEST_MODULE) and not matches(p, every_cover)]


def select(entries, layers, changed=None):
    """The entries of the wanted layers; with changed paths, only the integration entries those paths reach."""
    picked = [e for e in entries if e.layer in layers]
    if changed is None:
        return picked
    every_cover = sorted({glob for e in entries if e.layer == "integration" for glob in e.covers})
    if unknown_code(changed, every_cover):
        return picked
    changed = set(changed)
    return [e for e in picked if e.layer != "integration" or e.module in changed or matches_any(changed, e.covers)]


def matches_any(paths, globs):
    return any(matches(path, globs) for path in paths)


def chunks(entries):
    """Test-id lists in discovery order: a unit or contract class whole, any other test alone, so the slow tests
    spread over the workers and the shards."""
    out, cls = [], None
    for entry in entries:
        if entry.layer in FAST and entry.cls == cls:
            out[-1].append(entry.id)
        else:
            out.append([entry.id])
        cls = entry.cls if entry.layer in FAST else None
    return out


def shard(items, spec):
    """The I-th of N interleaved slices of items, for --shard I/N."""
    index, count = (int(part) for part in spec.split("/"))
    if not 1 <= index <= count:
        raise ValueError(f"--shard {spec}: I runs from 1 to N")
    return items[index - 1::count]


def changed_files(ref):
    """Paths that differ between ref and the working tree, untracked files included; None when git cannot read ref."""
    diff = subprocess.run(["git", "-C", str(KIT), "diff", "--name-only", "--no-renames", "-z", ref, "--"],
                          capture_output=True, text=True)
    if diff.returncode != 0:
        return None
    others = subprocess.run(["git", "-C", str(KIT), "ls-files", "--others", "--exclude-standard", "-z"],
                            capture_output=True, text=True, check=True)
    return sorted({p for p in (diff.stdout + others.stdout).split("\0") if p})


class Recorder(unittest.TestResult):
    """A picklable record of one chunk: counts, each failure's text, each skip's reason and each test's seconds."""

    def __init__(self):
        super().__init__()
        self.buffer = True  # a test's own output shows only with its failure, never interleaved across workers
        self.seconds, self.outcomes, self._start = {}, {}, {}

    def startTest(self, test):
        self._start[test.id()] = time.perf_counter()
        super().startTest(test)

    def stopTest(self, test):
        super().stopTest(test)
        self.seconds[test.id()] = time.perf_counter() - self._start.pop(test.id(), time.perf_counter())
        self.outcomes.setdefault(test.id(), "pass")

    def _mark(self, test, outcome):
        self.outcomes[getattr(test, "test_case", test).id()] = outcome

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._mark(test, "fail")

    def addError(self, test, err):
        super().addError(test, err)
        self._mark(test, "error")

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            self._mark(test, "fail" if issubclass(err[0], test.failureException) else "error")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._mark(test, "skip")

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self._mark(test, "fail")

    def record(self):
        return {"run": self.testsRun,
                "failures": [(str(t), text) for t, text in self.failures],
                "errors": [(str(t), text) for t, text in self.errors],
                "unexpected": [str(t) for t in self.unexpectedSuccesses],
                "skipped": [(t.id(), reason) for t, reason in self.skipped],
                "seconds": self.seconds, "outcomes": self.outcomes}


def run_chunk(ids):
    result = Recorder()
    unittest.defaultTestLoader.loadTestsFromNames(ids).run(result)
    return result.record()


def run_tests(tests):
    result = Recorder()
    unittest.TestSuite(tests).run(result)
    return result.record()


def _worker_init(path):
    sys.path.insert(0, path)


def run_all(chunk_list, serial_chunks, jobs, extra=(), start=TESTS):
    """Records of the parallel chunks, then of the serial ones, then of the tests in extra (the failed imports)."""
    records = []
    if chunk_list:
        if jobs <= 1:
            records += [run_chunk(ids) for ids in chunk_list]
        else:
            context = multiprocessing.get_context("spawn")  # the same start on Linux and macOS
            with context.Pool(min(jobs, len(chunk_list)), initializer=_worker_init, initargs=(str(start),)) as pool:
                records += list(pool.imap_unordered(run_chunk, chunk_list))
    records += [run_chunk(ids) for ids in serial_chunks]
    if extra:
        records.append(run_tests(list(extra)))
    return records


def merge(records):
    total = {"run": 0, "failures": [], "errors": [], "unexpected": [], "skipped": [], "seconds": {}, "outcomes": {}}
    for record in records:
        total["run"] += record["run"]
        for key in ("failures", "errors", "unexpected", "skipped"):
            total[key] += record[key]
        total["seconds"].update(record["seconds"])
        total["outcomes"].update(record["outcomes"])
    return total


def summary(total, elapsed, durations=0):
    """unittest's report: each failure and error, `Ran N tests in`, then OK or FAILED with the counts."""
    out = io.StringIO()
    for flavour, key in (("ERROR", "errors"), ("FAIL", "failures")):
        for description, text in total[key]:
            out.write(f"{SEPARATOR1}\n{flavour}: {description}\n{SEPARATOR2}\n{text}\n")
    out.write(f"{SEPARATOR2}\nRan {total['run']} test{'' if total['run'] == 1 else 's'} in {elapsed:.3f}s\n\n")
    counts = [f"failures={len(total['failures'])}" if total["failures"] else "",
              f"errors={len(total['errors'])}" if total["errors"] else "",
              f"skipped={len(total['skipped'])}" if total["skipped"] else "",
              f"unexpected successes={len(total['unexpected'])}" if total["unexpected"] else ""]
    counts = ", ".join(c for c in counts if c)
    ok = not (total["failures"] or total["errors"] or total["unexpected"])
    out.write(("OK" if ok else "FAILED") + (f" ({counts})" if counts else "") + "\n")
    reasons = {}
    for _, reason in total["skipped"]:
        reasons[reason] = reasons.get(reason, 0) + 1
    for reason, count in sorted(reasons.items(), key=lambda item: (-item[1], item[0])):
        out.write(f"run_tests: skipped {count}: {reason}\n")
    if durations:
        out.write(f"run_tests: slowest {durations}\n")
        for tid, seconds in sorted(total["seconds"].items(), key=lambda item: -item[1])[:durations]:
            out.write(f"  {seconds:8.3f}s  {tid}\n")
    return out.getvalue(), ok


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--layer", default=",".join(LAYERS), help="comma-separated layers (default: all)")
    parser.add_argument("--changed-from", metavar="REF", help="run only the integration classes the changes reach")
    parser.add_argument("--shard", metavar="I/N", help="run the I-th of N slices of the selected chunks")
    parser.add_argument("--jobs", type=int, default=os.cpu_count() or 1, help="worker processes (default: CPUs)")
    parser.add_argument("--durations", type=int, default=0, metavar="N", help="list the N slowest tests")
    parser.add_argument("--json", metavar="FILE", help="write every test's layer, seconds and outcome")
    parser.add_argument("--list", action="store_true", help="print the selected tests with their layers, run none")
    parser.add_argument("--start", default=str(TESTS), help="the folder of the test modules (default: this kit's)")
    parser.add_argument("files", nargs="*", metavar="FILE", help="test modules under --start to run whole")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    layers = [layer for layer in args.layer.split(",") if layer]
    unknown = [layer for layer in layers if layer not in LAYERS]
    if unknown or not layers:
        print(f"run_tests: unknown layer {', '.join(unknown) or '(none)'}; the layers: {', '.join(LAYERS)}",
              file=sys.stderr)
        return 2
    start = Path(args.start).resolve()
    outside = [name for name in args.files if Path(name).resolve().parent != start or not name.endswith(".py")]
    if outside:
        print(f"run_tests: not a test module under {start}: {', '.join(outside)}", file=sys.stderr)
        return 2
    entries, failed, problems = discover(start, args.files)
    if args.files:
        layers = list(LAYERS) + [None]
    if problems:
        print("run_tests: tag every test class (KIT-077):\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2
    changed = None
    if args.changed_from:
        changed = changed_files(args.changed_from)
        if changed is None:
            print(f"run_tests: git cannot diff against {args.changed_from}", file=sys.stderr)
            return 2
    picked = select(entries, set(layers), changed)
    parallel = chunks([e for e in picked if e.layer != "performance"])
    serial = chunks([e for e in picked if e.layer == "performance"])
    try:
        if args.shard:
            parallel, serial = shard(parallel, args.shard), shard(serial, args.shard)
    except ValueError as error:
        print(f"run_tests: {error}", file=sys.stderr)
        return 2
    if args.shard and args.shard.split("/")[0] != "1":
        failed = []  # an import failure reports once, on shard 1
    # the slow layers first, so the long chunks start while the short ones fill the gaps
    layer_of = {e.id: e.layer for e in entries}
    parallel.sort(key=lambda ids: layer_of[ids[0]] not in SLOW)
    count = sum(map(len, parallel + serial))
    scope = (f"{len(args.files)} files" if args.files else f"layers {','.join(layers)}") + (
        f", changes from {args.changed_from}" if changed is not None else "") + (
        f", shard {args.shard}" if args.shard else "")
    if args.list:
        for ids in parallel + serial:
            for tid in ids:
                print(f"{layer_of[tid] or 'untagged':<12} {tid}")
        print(f"run_tests: {count} tests ({scope})")
        return 0
    if not count and not failed:
        if changed is not None or args.shard:
            print(f"run_tests: nothing to run ({scope}): no selected test is reached by the changes or this shard")
            return 0
        print(f"run_tests: no test selected ({scope})", file=sys.stderr)
        return 2
    jobs = max(1, args.jobs)
    print(f"run_tests: {count} tests in {len(parallel) + len(serial)} chunks, {jobs} workers ({scope})", flush=True)
    began = time.perf_counter()
    total = merge(run_all(parallel, serial, jobs, failed, start))
    text, ok = summary(total, time.perf_counter() - began, args.durations)
    sys.stdout.write(text)
    if args.json:
        rows = [{"id": tid, "layer": layer_of.get(tid) or "untagged",
                 "seconds": round(total["seconds"].get(tid, 0.0), 3), "outcome": outcome}
                for tid, outcome in sorted(total["outcomes"].items())]
        Path(args.json).write_text(json.dumps({"scope": scope, "tests": rows}, indent=1) + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
