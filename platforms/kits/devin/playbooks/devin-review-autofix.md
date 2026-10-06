# Devin Review autofix beside a Claude-reviewed loop

Applies when a project runs the review loop (Claude reviews, Devin implements) and also enables Devin Review.

- Setting (verified 2026-10-06, docs.devin.ai/work-with-devin/devin-review): Settings > Devin > Pull requests > Responding to bots. Set the mode to Selected only and add `devin-ai-integration[bot]` to the allowlist; admins turn on "Auto-fix review findings" under Settings > Review.
- Forbidden setting: respond to all bots (the "All bots" mode). The Claude orchestrator's review comments would then start a second Devin writer on the same branch while a fix round is open.
- Single-writer rule: at any time one writer owns a branch, the loop's child during a fix round, or Devin Review autofix, never both. Autofix ignores the "No Issues Found" summary and acts on actual findings only.
- When the loop gates a PR, let the loop's fix round apply findings; use autofix only on PRs outside the loop.
- Procedure of the loop itself: the project's review-loop README.
