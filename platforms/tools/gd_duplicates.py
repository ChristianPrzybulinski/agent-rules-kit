#!/usr/bin/env python3
"""Advisory structural duplicates of changed GDScript functions (KIT-033).

Usage: gd_duplicates.py [--base REF] [--all] [--threshold S] [FILE...]

Every function of the tracked .gd files outside addons/ is parsed with gdtoolkit (pinned 4.5.0) and normalised:
names become a placeholder except the called name, numbers and type hints become placeholders, string literals stay.
Every subtree is fingerprinted, and a pair scores the Jaccard similarity of its two fingerprint sets. Pairs at
0.82 or above are reported when both functions have at least MIN_LINES lines and MIN_NODES nodes.

Without FILE or --all, the functions whose lines changed in `git diff -U0 <base>...HEAD` are compared with every
function in the tree; with FILE, every function of those files is; with --all, every pair in the tree. stdout holds
one `score path:line function path:line function` line per pair, highest first; stderr the notices. Exit 0; with
--threshold S, exit 1 when a pair reaches S and exit 2 when gdtoolkit is missing. A bad ref exits 2.

Parsing is most of the run, so the fingerprints of each file are cached by its content hash under
$XDG_CACHE_HOME/ai-kit/gd-duplicates (default ~/.cache); an entry unused for CACHE_DAYS is pruned, and the
directory can be deleted at any time.
"""
import argparse
import base64
import bisect
import functools
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from array import array
from contextlib import suppress
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

from complexity import changed_lines  # one definition of a changed line for both advisory tools

try:
    from gdtoolkit.parser import parser as GD_PARSER
    from lark import Token
except ImportError:  # fail open: main() names what is missing
    GD_PARSER = None

SCORE_MIN = 0.82
MIN_LINES = 4
MIN_NODES = 40
EXCLUDED = ("addons/",)  # third-party Godot plugins
CACHE_VERSION = 1  # bump when walk() or leaf() changes what a fingerprint holds
CACHE_DAYS = 30
sys.setrecursionlimit(20000)  # deep expression trees


@dataclass(frozen=True)
class Function:
    path: str
    name: str
    start: int
    end: int  # inclusive: the line of the last token
    prints: frozenset


def notice(text):
    print(f"gd_duplicates: {text}", file=sys.stderr)


def digest(text):
    return int.from_bytes(hashlib.blake2b(text.encode(), digest_size=8).digest(), "big")


def leaf(token, keep_name):
    if token.type == "NAME":
        return "n:" + token if keep_name else "@id"
    if token.type == "NUMBER":
        return "@num"
    if token.type == "TYPE_HINT":
        return "@type"
    return "t:" + token  # keywords, operators and string literals stay as written


def walk(node, prints, keep=None):
    """(hash, node count) of the normalised subtree; every subtree hash goes into prints.

    keep "self" keeps this NAME; keep "last" keeps the last child of this getattr (the called method)."""
    if isinstance(node, Token):
        value = digest(leaf(node, keep == "self"))
        prints.add(value)
        return value, 1
    kids = node.children
    keeps = [None] * len(kids)
    if kids and node.data == "standalone_call":
        keeps[0] = "self"
    elif kids and node.data == "getattr_call":
        keeps[0] = "last"
    elif kids and node.data == "getattr" and keep == "last":
        keeps[-1] = "self"
    hashes, count = [], 1
    for kid, kid_keep in zip(kids, keeps):
        value, size = walk(kid, prints, kid_keep)
        hashes.append(str(value))
        count += size
    value = digest(f"{node.data}({','.join(hashes)})")
    prints.add(value)
    return value, count


def parse(text):
    """(name, start, end, nodes, prints) of every function in one .gd source, before the size minimums."""
    found, stack = [], [GD_PARSER.parse(text, gather_metadata=True)]
    while stack:
        node = stack.pop()
        if isinstance(node, Token):
            continue
        stack.extend(node.children)
        if node.data != "func_def":
            continue
        prints = set()
        _, nodes = walk(node, prints)
        # meta.end_line runs past trailing blank lines into the next declaration; the last token does not.
        end = max(t.end_line for t in node.scan_values(lambda v: isinstance(v, Token)))
        found.append((str(node.children[0].children[0]), node.meta.line, end, nodes, frozenset(prints)))
    return found


def cache_dir():
    root = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    return Path(root, "ai-kit", "gd-duplicates")


@functools.lru_cache(maxsize=None)
def gdtoolkit_version():
    try:
        return metadata.version("gdtoolkit")
    except metadata.PackageNotFoundError:
        return "unknown"


def cache_entry(cache, text):
    key = f"{CACHE_VERSION}\0{gdtoolkit_version()}\0{text}"
    return cache / (hashlib.sha256(key.encode()).hexdigest() + ".json")


def cache_load(entry):
    try:
        rows = json.loads(entry.read_text(encoding="utf-8"))
        os.utime(entry)  # a used entry is never pruned
    except (OSError, ValueError):
        return None
    return [(n, s, e, k, frozenset(array("Q", base64.b64decode(p)))) for n, s, e, k, p in rows]


def cache_store(entry, rows):
    """Write the entry whole or not at all; a cache that cannot be written only costs the next run its parse."""
    data = [[n, s, e, k, base64.b64encode(array("Q", sorted(p)).tobytes()).decode()] for n, s, e, k, p in rows]
    temp = None
    try:
        entry.parent.mkdir(parents=True, exist_ok=True)
        handle, temp = tempfile.mkstemp(dir=entry.parent, suffix=".tmp")
        with os.fdopen(handle, "w", encoding="utf-8") as out:
            json.dump(data, out)
        os.replace(temp, entry)
    except OSError:
        if temp:
            with suppress(OSError):
                os.unlink(temp)


def cache_prune(cache):
    cutoff = time.time() - CACHE_DAYS * 86400
    for entry in cache.glob("*"):  # entries and the temp file of a run that crashed while writing
        with suppress(OSError):
            if entry.stat().st_mtime < cutoff:
                entry.unlink()


def file_functions(path, cache):
    """Functions of one .gd file at or above the size minimums, parsed or read from the cache."""
    text = Path(path).read_text(encoding="utf-8")
    entry = cache_entry(cache, text)
    rows = cache_load(entry)
    if rows is None:
        rows = parse(text)
        cache_store(entry, rows)
    return [Function(path, n, s, e, p) for n, s, e, k, p in rows if e - s + 1 >= MIN_LINES and k >= MIN_NODES]


def score(left, right):
    common = len(left.prints & right.prints)
    return common / (len(left.prints) + len(right.prints) - common)


def pairs(queries, corpus):
    """(score, query, other) for every pair at SCORE_MIN or above, each unordered pair once."""
    corpus = sorted(corpus, key=lambda f: len(f.prints))
    sizes = [len(f.prints) for f in corpus]
    seen, found = set(), []
    for query in queries:
        size = len(query.prints)  # Jaccard >= s needs the smaller set to hold s of the larger one
        low, high = bisect.bisect_left(sizes, size * SCORE_MIN), bisect.bisect_right(sizes, size / SCORE_MIN)
        for other in corpus[low:high]:
            key = frozenset(((query.path, query.start), (other.path, other.start)))
            if len(key) == 1 or key in seen:
                continue
            seen.add(key)
            value = score(query, other)
            if value >= SCORE_MIN:
                found.append((value, query, other))
    return sorted(found, key=lambda p: (-p[0], p[1].path, p[1].start, p[2].path, p[2].start))


def git_lines(*args):
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if result.returncode:
        notice(f"git {args[0]} failed: {result.stderr.strip()}")
        sys.exit(2)
    return result.stdout


def main():
    ap = argparse.ArgumentParser(description="Advisory structural duplicates of changed GDScript functions")
    ap.add_argument("files", nargs="*", help="compare every function of these files instead of the changed ones")
    ap.add_argument("--base", default="origin/main", help="ref the change is compared against (default origin/main)")
    ap.add_argument("--all", action="store_true", help="report every pair in the tree")
    ap.add_argument("--threshold", type=float, help="exit 1 when a pair's score reaches S")
    args = ap.parse_args()
    files = [os.path.abspath(p) for p in args.files]
    os.chdir(git_lines("rev-parse", "--show-toplevel").strip())
    tree = [p for p in git_lines("ls-files", "--", "*.gd").splitlines() if not p.startswith(EXCLUDED)]
    if args.all:
        wanted = {p: None for p in tree}
    elif files:
        wanted = {os.path.relpath(p): None for p in files}
    else:
        wanted = {p: n for p, n in changed_lines(args.base).items() if p.endswith(".gd") and not p.startswith(EXCLUDED)}
    wanted = {p: n for p, n in wanted.items() if Path(p).is_file()}
    if not wanted:
        notice("no changed .gd function to compare")
        return 0
    if GD_PARSER is None:
        notice(f"gdtoolkit not available (pip install gdtoolkit); duplicates not measured for {len(wanted)} .gd file(s)")
        return 2 if args.threshold is not None else 0
    corpus, failed, cache = [], [], cache_dir()
    for path in sorted(set(tree) | set(wanted)):
        try:
            corpus += file_functions(path, cache)
        except Exception as error:  # a file gdtoolkit cannot parse is named, never fatal
            failed.append(f"{path}: {type(error).__name__}")
    cache_prune(cache)
    for text in failed[:3]:
        notice(f"not parsed: {text}")
    queries = [f for f in corpus if f.path in wanted and (wanted[f.path] is None or
                                                          any(f.start <= n <= f.end for n in wanted[f.path]))]
    found = pairs(queries, corpus)
    for value, left, right in found:
        print(f"{value:.3f} {left.path}:{left.start} {left.name} {right.path}:{right.start} {right.name}")
    notice(f"{len(found)} pair(s) at >= {SCORE_MIN} for {len(queries)} function(s) against {len(corpus)} "
           f"in {len(set(tree) | set(wanted)) - len(failed)} file(s); {len(failed)} file(s) not parsed")
    if args.threshold is None:
        return 0
    return 1 if any(value >= args.threshold for value, _, _ in found) else 0


if __name__ == "__main__":
    sys.exit(main())
