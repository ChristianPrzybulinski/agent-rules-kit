#!/usr/bin/env python3
"""release.yml's guard (KIT-077): a release tag stands only on a commit where ci-full passed. The guard reads the
ci-full runs of the tag's commit through `gh api`: a green run passes; a queued or running one is waited for, every
30 s up to --wait minutes; otherwise the guard deletes the tag it runs for and fails, so neither the tag nor a release
stays on a commit the full gate never passed. A gh error deletes nothing.

Usage: release_guard.py --repo OWNER/NAME --sha SHA --tag TAG [--wait MINUTES] [--poll SECONDS]   (gh reads GH_TOKEN)
Exit 0 when ci-full passed on SHA, 1 when it did not (the tag is deleted), 2 when gh fails or the wait runs out.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time

WORKFLOW = "ci-full.yml"
POLL_S = 30


def verdict(runs: list[dict]) -> str:
    """pass when one ci-full run on the commit succeeded, wait while one is not completed, else fail."""
    if any(run.get("conclusion") == "success" for run in runs):
        return "pass"
    if any(run.get("status") != "completed" for run in runs):
        return "wait"
    return "fail"


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout


def runs_of(repo: str, sha: str) -> list[dict]:
    text = gh("api", f"repos/{repo}/actions/workflows/{WORKFLOW}/runs?head_sha={sha}&per_page=100",
              "--jq", "[.workflow_runs[] | {id, status, conclusion}]")
    return json.loads(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--repo", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--wait", type=float, default=20, help="minutes to wait for a running ci-full (default 20)")
    parser.add_argument("--poll", type=float, default=POLL_S, help=f"seconds between reads (default {POLL_S})")
    args = parser.parse_args(argv)
    deadline = time.monotonic() + args.wait * 60
    try:
        while True:
            runs = runs_of(args.repo, args.sha)
            state = verdict(runs)
            print(f"release guard: {len(runs)} {WORKFLOW} runs on {args.sha}: {state}")
            if state == "pass":
                return 0
            if state == "fail":
                gh("api", "-X", "DELETE", f"repos/{args.repo}/git/refs/tags/{args.tag}")
                print(f"::error title=release guard::no green {WORKFLOW} run on {args.sha}; tag {args.tag} deleted. "
                      f"Run {WORKFLOW} on that commit (it runs on every push to main), then push the tag again")
                return 1
            if time.monotonic() >= deadline:
                print(f"::error title=release guard::{WORKFLOW} still runs on {args.sha} after {args.wait:g} min; the "
                      "tag stays and no release is made: rerun this workflow once it finishes")
                return 2
            time.sleep(args.poll)
    except subprocess.CalledProcessError as error:
        print(f"::error title=release guard::gh failed ({error.returncode}): {error.stderr.strip()[:300]}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
