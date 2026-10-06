#!/usr/bin/env python3
"""Per-batch review-loop KPIs from a ledger.csv. Usage: kpi.py LEDGER.csv [--batch ID] [--json]

Reads the loop ledger header (at,batch,role,kind,pr,issue,sha,round,model,duration_s,usd,note) and, from
the `note` column of kind=review rows, the space-separated tokens verdict=<approved|flagged|needs-product|
needs-human>, findings=<n> and spec=<n>. One line (or JSON object) per batch: first-pass approval, rounds
per PR, share of findings owned by spec, median minutes from the first row of an issue to its approval.
"""
import argparse
import csv
import json
import statistics
import sys
from datetime import datetime

HEADER = ["at", "batch", "role", "kind", "pr", "issue", "sha", "round", "model", "duration_s", "usd", "note"]


def tokens(note):
    return dict(t.split("=", 1) for t in (note or "").split() if "=" in t)


def pct(num, den):
    return round(100.0 * num / den, 1) if den else None


def metrics(batch, rows):
    reviews = [r for r in rows if r["kind"] == "review" and r["pr"]]
    by_pr = {}
    for r in reviews:  # rows are sorted by time
        by_pr.setdefault(r["pr"], []).append(r)
    decided = [p for p, rs in by_pr.items() if "verdict" in tokens(rs[0]["note"])]
    approved = [p for p in decided if tokens(by_pr[p][0]["note"])["verdict"] == "approved"]
    counts = [len(rs) for rs in by_pr.values()]
    pairs = [(int(t["spec"]), int(t["findings"])) for t in (tokens(r["note"]) for r in reviews)
             if t.get("spec", "").isdigit() and t.get("findings", "").isdigit()]
    spec, findings = sum(p[0] for p in pairs), sum(p[1] for p in pairs)
    greens = []
    for pr, rs in by_pr.items():
        done = [r for r in rs if tokens(r["note"]).get("verdict") == "approved"]
        if not done:
            continue
        same = [r for r in rows if (r["issue"] and r["issue"] == done[0]["issue"]) or (not done[0]["issue"] and r["pr"] == pr)]
        start = min(r["_t"] for r in same)
        greens.append((done[0]["_t"] - start).total_seconds() / 60.0)
    return {
        "batch": batch, "prs": len(by_pr),
        "first_pass_approval": pct(len(approved), len(decided)), "approved": len(approved), "decided": len(decided),
        "rounds_per_pr": round(sum(counts) / len(counts), 1) if counts else None, "rounds_max": max(counts, default=None),
        "spec_findings": pct(spec, findings), "spec": spec, "findings": findings,
        "median_time_to_green_min": round(statistics.median(greens), 1) if greens else None,
    }


def line(m):
    def f(key, text):
        return text if m[key] is not None else "n/a"
    return (f"batch {m['batch']}: prs={m['prs']} "
            f"first_pass_approval={f('first_pass_approval', str(m['first_pass_approval']) + '%')} ({m['approved']}/{m['decided']}) "
            f"rounds_per_pr={f('rounds_per_pr', str(m['rounds_per_pr']))} (max {m['rounds_max']}) "
            f"spec_findings={f('spec_findings', str(m['spec_findings']) + '%')} ({m['spec']}/{m['findings']}) "
            f"median_time_to_green={f('median_time_to_green_min', str(m['median_time_to_green_min']) + ' min')}")


def main():
    ap = argparse.ArgumentParser(description="Per-batch review-loop KPIs from a ledger.csv")
    ap.add_argument("ledger")
    ap.add_argument("--batch")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    try:
        with open(args.ledger, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames != HEADER:
                print(f"kpi: {args.ledger}: header is not {','.join(HEADER)}", file=sys.stderr)
                return 2
            rows = list(reader)
    except OSError as exc:
        print(f"kpi: cannot read ledger: {exc}", file=sys.stderr)
        return 2
    for r in rows:
        r["_t"] = datetime.fromisoformat(r["at"])
    rows.sort(key=lambda r: r["_t"])
    batches = {}
    for r in rows:
        if not args.batch or r["batch"] == args.batch:
            batches.setdefault(r["batch"], []).append(r)
    results = [metrics(b, rs) for b, rs in batches.items()]
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for m in results:
            print(line(m))
    return 0


if __name__ == "__main__":
    sys.exit(main())
