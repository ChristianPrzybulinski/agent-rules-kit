#!/usr/bin/env python3
"""Keyed-CSV git merge driver (agent-rules-kit KIT-074): merges a translation CSV row by row, by key. Stdlib only.

`merge=union` on a translation CSV keeps a branch's stale row beside the other side's edited row of the same key and
reports no conflict; this driver merges the file key by key instead and reports a real conflict as one.

Setup, once per clone (git config is not versioned; platforms/tools/sync-project.sh of agent-rules-kit vendors this
file into .github/merge-drivers/ and prints the step while it is missing):

    git config merge.keyed-csv.name "keyed CSV merge"
    git config merge.keyed-csv.driver "python3 .github/merge-drivers/keyed_csv_merge.py --marker-size %L --path %P %O %A %B"

and one `.gitattributes` line per file or glob:  `client/i18n/*.csv merge=keyed-csv`. Add `--key-column N` to the
driver for a key outside column 1. In a clone without the driver git merges the file as text, so a conflict shows.

The rule. Record 1 is the header; every other non-blank record is one row, kept byte for byte, whose key is its
field N (1-based, parsed as CSV, so a quoted key may hold a comma and a quoted value may span lines). For each key,
with b, o, t its rows in the base, ours and theirs (or none): o == t gives o; o == b gives t; t == b gives o; anything
else is a conflict. A key twice on one side is a conflict, and so are two different headers. Order: when every side
is sorted by key, the result is sorted; otherwise it keeps our order and places each of their new keys after the key
before it on their side. Line ending: ours (CRLF and LF rows compare equal). A conflict is written in place with git's
markers (ours, then theirs) and exits 1; an input that does not parse is merged as text by `git merge-file`, with a
warning. The record split reads every `"` as a quote, wherever it stands, so a `"` inside an unquoted field (an inch
mark: `5" screen`) leaves the file unparsable and the whole file merges as text; write that field quoted with the
mark doubled (`"5"" screen"`) to keep the keyed merge.

Usage: keyed_csv_merge.py [--key-column N] [--marker-size N] [--path P] BASE OURS THEIRS
Writes the result to OURS. Exit 0 clean, 1 conflicts, 2 usage error.
"""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path

HEADER = "(header)"  # the conflict label of two different headers


def records(text: str) -> list[str]:
    """The CSV records of text, each without its line ending; a newline inside quotes stays in its record."""
    out: list[str] = []
    start = 0
    quoted = False
    for i, char in enumerate(text):
        if char == '"':
            quoted = not quoted
        elif char == "\n" and not quoted:
            out.append(text[start:i])
            start = i + 1
    if quoted:
        raise ValueError("a quoted field is not closed")
    if start < len(text):
        out.append(text[start:])
    return [r[:-1] if r.endswith("\r") else r for r in out]


def key_of(record: str, column: int) -> str:
    fields = next(csv.reader([record]), [])
    if len(fields) < column:
        raise ValueError(f"a row has no column {column}: {record[:60]!r}")
    return fields[column - 1]


def parse(text: str, column: int) -> tuple[tuple[str, ...], dict[str, tuple[str, ...]], list[str]]:
    """(header records, {key: its rows}, the keys in file order) of one side; an empty text has none."""
    rows = [r for r in records(text) if r.strip()]
    if not rows:
        return (), {}, []
    by_key: dict[str, tuple[str, ...]] = {}
    order: list[str] = []
    for row in rows[1:]:
        key = key_of(row, column)
        if key not in by_key:
            order.append(key)
        by_key[key] = by_key.get(key, ()) + (row,)
    return (rows[0],), by_key, order


def pick(base, ours, theirs):
    """The 3-way rule for one key or the header: (result, conflict); () is no row."""
    if ours == theirs:
        return ours, False
    if ours == base:
        return theirs, False
    if theirs == base:
        return ours, False
    return None, True


def is_sorted(order: list[str]) -> bool:
    return all(a < b for a, b in zip(order, order[1:]))


def merged_order(ours: list[str], theirs: list[str], keys: set[str], sort: bool) -> list[str]:
    if sort:
        return sorted(keys)
    out = [k for k in ours if k in keys]
    placed = set(out)
    for i, key in enumerate(theirs):
        if key in placed or key not in keys:
            continue
        before = next((k for k in reversed(theirs[:i]) if k in placed), None)
        out.insert(0 if before is None else out.index(before) + 1, key)
        placed.add(key)
    return out


def merge(base: str, ours: str, theirs: str, key_column: int = 1, labels: tuple[str, str] = ("ours", "theirs"),
          marker_size: int = 7) -> tuple[str, list[str]]:
    """(the merged text, the sorted conflicting keys). A conflict sits in the text between git's markers. Raises
    ValueError or csv.Error when a side does not parse."""
    sides = [parse(text, key_column) for text in (base, ours, theirs)]
    nl = "\r\n" if "\r\n" in ours else "\n"
    conflicts: list[str] = []
    lines: list[str] = []

    def block(ours_rows, theirs_rows):
        lines.extend(["<" * marker_size + " " + labels[0], *ours_rows, "=" * marker_size, *theirs_rows,
                      ">" * marker_size + " " + labels[1]])

    head, conflict = pick(*(header for header, _, _ in sides))
    if conflict:
        conflicts.append(HEADER)
        block(sides[1][0], sides[2][0])
    else:
        lines.extend(head)
    keys = set().union(*(rows for _, rows, _ in sides))
    results = {}
    for key in keys:
        rows = [side[1].get(key, ()) for side in sides]
        row, conflict = pick(*rows)
        if conflict or any(len(r) > 1 for r in rows[1:]):
            results[key] = None
            conflicts.append(key)
        elif row:
            results[key] = row
    sort = all(is_sorted(order) for _, _, order in sides)
    for key in merged_order(sides[1][2], sides[2][2], set(results), sort):
        if results[key] is None:
            block(sides[1][1].get(key, ()), sides[2][1].get(key, ()))
        else:
            lines.extend(results[key])
    return "".join(line + nl for line in lines), sorted(conflicts, key=lambda k: (k != HEADER, k))


def text_merge(base: Path, ours: Path, theirs: Path, marker_size: int) -> int:
    result = subprocess.run(["git", "merge-file", f"--marker-size={marker_size}", "-L", "ours", "-L", "base",
                             "-L", "theirs", str(ours), str(base), str(theirs)])
    return 0 if result.returncode == 0 else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="keyed-CSV git merge driver (KIT-074); see the module text")
    parser.add_argument("--key-column", type=int, default=1, help="the key's column, 1-based (default 1)")
    parser.add_argument("--marker-size", type=int, default=7, help="conflict marker length, git's %%L (default 7)")
    parser.add_argument("--path", default="", help="the file's path in the repository, git's %%P (messages only)")
    parser.add_argument("base")
    parser.add_argument("ours", help="the file git reads the result from")
    parser.add_argument("theirs")
    args = parser.parse_args(argv)  # exits 2 on a usage error
    if args.key_column < 1 or args.marker_size < 1:
        parser.error("--key-column and --marker-size must be 1 or more")
    paths = [Path(p) for p in (args.base, args.ours, args.theirs)]
    try:
        texts = [p.read_bytes().decode("utf-8") for p in paths]
        text, conflicts = merge(*texts, key_column=args.key_column, marker_size=args.marker_size)
    except (OSError, UnicodeDecodeError, ValueError, csv.Error) as err:
        print(f"keyed_csv_merge: {args.path or args.ours}: {err}; warning: the whole file merges as text, not by key "
              '(a " counts as a quote wherever it stands: quote a field that holds one and double it, "5"" screen")',
              file=sys.stderr)
        return text_merge(*paths, args.marker_size)
    paths[1].write_bytes(text.encode("utf-8"))
    if conflicts:
        print(f"keyed_csv_merge: {args.path or args.ours}: conflicting keys: {', '.join(conflicts)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
