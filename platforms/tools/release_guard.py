#!/usr/bin/env python3
"""release.yml's guard (KIT-077): a release is published only from a commit where ci-full passed. The guard reads the
ci-full runs of the tagged commit through `gh api` and waits, every --poll seconds up to --wait minutes, while there is
none yet (the tag push can come before the run is created) or one is queued or in progress. A green run passes. A
completed run that is not green, or the wait running out, fails the job, so no release is published. The guard never
deletes or moves the tag: the ruleset protect-release-tags forbids deleting a v* tag, so the tag stays, and the release
follows by re-running release.yml once ci-full is green on that commit (`gh run rerun <id>`), or with the next patch
version.

Usage: release_guard.py --repo OWNER/NAME --sha SHA --tag TAG [--wait MINUTES] [--poll SECONDS]   (gh reads GH_TOKEN)
Exit 0 when ci-full passed on SHA, 1 when it did not or the wait ran out, 2 when gh fails.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

WORKFLOW = "ci-full.yml"
POLL_S = 30


def verdict(runs: list[dict]) -> str:
    """pass when one ci-full run on the commit succeeded; wait while there is none or one is not completed; else
    fail (every run completed, none green)."""
    if any(run.get("conclusion") == "success" for run in runs):
        return "pass"
    if not runs or any(run.get("status") != "completed" for run in runs):
        return "wait"
    return "fail"


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout


def runs_of(repo: str, sha: str) -> list[dict]:
    text = gh("api", f"repos/{repo}/actions/workflows/{WORKFLOW}/runs?head_sha={sha}&per_page=100",
              "--jq", "[.workflow_runs[] | {id, status, conclusion}]")
    return json.loads(text)


def refusal(why: str, tag: str) -> str:
    rerun = os.environ.get("GITHUB_RUN_ID")
    command = f"gh run rerun {rerun}" if rerun else "gh run rerun <this run's id>"
    return (f"::error title=release guard::{why}; no release is published. Tag {tag} stays (the ruleset "
            f"protect-release-tags forbids deleting it): once {WORKFLOW} is green on that commit, re-run this workflow "
            f"({command}), or release the next patch version")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--repo", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--wait", type=float, default=20, help="minutes to wait for a ci-full run (default 20)")
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
                found = ", ".join(sorted({str(run.get("conclusion")) for run in runs}))
                print(refusal(f"no green {WORKFLOW} run on {args.sha} (completed: {found})", args.tag))
                return 1
            if time.monotonic() >= deadline:
                print(refusal(f"no completed green {WORKFLOW} run on {args.sha} after {args.wait:g} min "
                              f"({len(runs)} runs, none completed green)", args.tag))
                return 1
            time.sleep(args.poll)
    except subprocess.CalledProcessError as error:
        print(f"::error title=release guard::gh failed ({error.returncode}): {error.stderr.strip()[:300]}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
