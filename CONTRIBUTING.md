# Contributing to agent-rules-kit

How to change the kit: where content goes, versioning, checks and evals. Sessions that work inside this repository read this file before a change; the always-on rules come from the installed `guardrails` plugin, so the root carries no `AGENTS.md` or `CLAUDE.md` (KIT-042).

## Outside contributors

This section is for people outside the project; the rest of the file is the procedure the maintainer and agent sessions follow.

- One person maintains the kit for their own projects, so a change is weighed against the setups it already serves. Answers come as time allows.
- Start with an issue, using the [bug report](https://github.com/ChristianPrzybulinski/agent-rules-kit/issues/new?template=bug_report.yml) or the [rule or skill proposal](https://github.com/ChristianPrzybulinski/agent-rules-kit/issues/new?template=rule_or_skill_proposal.yml) form. A bug report names the kit `VERSION`, the agent with its version and the operating system.
- Open a pull request only after the maintainer agrees to the change in its issue; a pull request without one may be closed unreviewed. Link the issue, keep to one concern, add a line under `## [Unreleased]` in [`CHANGELOG.md`](CHANGELOG.md), run `platforms/tools/check.sh` and fill in the PR checklist. The rest of this file says where each kind of content goes.
- A contribution is licensed under the repository's [MIT license](LICENSE).
- Report a vulnerability privately, as [`SECURITY.md`](SECURITY.md) says, never in an issue or pull request.

## What goes where

| Content | Location |
|---|---|
| always-on global behavior | `plugins/guardrails/AGENTS.md` |
| hook guard and format/lint hooks | `plugins/guardrails/hooks/hooks.json` |
| path-triggered rule | `plugins/<plugin>/rules/<name>.md` in the owning plugin |
| procedure or reference | `plugins/<plugin>/skills/<name>/` |
| subagent profile | `plugins/<plugin>/agents/<name>.md` in the plugin whose skills consume it |
| artifact skeleton | `plugins/<plugin>/templates/<prefix>-<name>.md` |
| executable, schema or project kit | `platforms/` |
| design principles, consumer layout, KIT records | `docs/` |

## Invariants

`platforms/ci/validations/check_kit.py` enforces these:

- The repository root holds no agent-facing content. A root `AGENTS.md` is refused: the root is the Devin meta-plugin, so it would load in every Devin session on top of `plugins/guardrails/AGENTS.md`.
- `.devin-plugin/plugin.json` requires every plugin and lists none as optional.
- Every directory under `plugins/` is a plugin with `.devin-plugin/plugin.json`, `.claude-plugin/plugin.json`, `plugin.json` and a generated `INDEX.md`; no other `INDEX.md` exists in the repository.
- `plugins/guardrails/` is the only plugin with `AGENTS.md` or `hooks/`.
- Plugin names are unique, and every referenced skill or agent is reachable through the dependency graph.
- `VERSION`, the meta-plugin manifest and every Devin, Codex and Claude manifest agree.
- Codex and Claude marketplace source paths are `./plugins/<name>`; plugin content has no managed duplicate.
- The Claude marketplace `renames` map sends each retired plugin name to its successor (or `null`), so an installed old name migrates on the next session (KIT-038).

## Versioning

A release sets one version in [`VERSION`](VERSION), in every manifest `"version"` field and in a [`CHANGELOG.md`](CHANGELOG.md) heading, then tags `vX.Y.Z`. The steps, in order:

1. Bump, on a branch from current `main` with a clean tree: `python3 platforms/tools/bump_version.py X.Y.Z` (KIT-019). It refuses a version that is not SemVer or not above `VERSION`, a dirty tree and an empty `## [Unreleased]`. It writes `VERSION`, replaces `"version": "<current>"` in every tracked `*plugin.json` and `*marketplace.json` (printing the count) and inserts `## [X.Y.Z] - <today>` under `## [Unreleased]` (`--date YYYY-MM-DD` overrides the date). Then run `check.sh`.
2. Open the release PR `chore(release): publish X.Y.Z`.
3. After the merge, tag the merge commit on `main` with an annotated tag: `git tag -a vX.Y.Z -m vX.Y.Z <commit>`, then `git push origin vX.Y.Z`.
4. The tag runs `.github/workflows/release.yml`, which validates tag == `VERSION` and creates the release from the CHANGELOG section. GitHub billing refuses its runs today (run 40978925050 on `v11.2.0`), so when no release appears, publish it by hand with the same notes and the workflow's title format: `python3 platforms/tools/bump_version.py --notes X.Y.Z > /tmp/kit-notes.md`, then `gh release create vX.Y.Z --verify-tag --title vX.Y.Z --notes-file /tmp/kit-notes.md`.

The layout of 10.x, kept unchanged by 11.0.0, is frozen until at least 2027-01-01 (principle "Layout stability" in [docs/design.md](docs/design.md)). A layout or installation-destination change is a SemVer MAJOR change and ships with a deprecation note in the release notes plus a migration in `bootstrap.sh` and `doctor.sh`. A content change is MINOR when it adds a rule, skill, reference, template, validator gate or document, and PATCH when it corrects one without changing routing. There is no separate layout version.

## Adding content

| Type | Steps |
|---|---|
| kit feature | only for a hook, `plugins/guardrails/AGENTS.md`, plugin structure or manifests, a check, gate or script behavior change, or a new or removed skill: after the owner confirms it, copy [`docs/features/TEMPLATE.md`](docs/features/TEMPLATE.md) to `docs/features/KIT-NNN-<slug>.md`, open issue `[KIT-NNN] <title>` with label `kit-feature`, list it in [`docs/features/README.md`](docs/features/README.md); the implementing PR closes the issue and its CHANGELOG line cites `KIT-NNN`. Any other change (a skill, rule, reference, template or doc text edit) needs only a CHANGELOG line, and the PR body carries the why |
| rule | create `plugins/<plugin>/rules/<name>.md` in the owning plugin with `description`, `trigger: glob|model_decision|manual`, and `globs` for a glob rule; body = one pointer line to the owning skill plus 8-12 always/never bullets, at most 40 lines; run `python3 platforms/tools/gen_index.py` to list it in the plugin's `INDEX.md` (never add non-rule files to `rules/` — Devin loads every `.md` there as a rule) |
| skill | search `plugins/guardrails/INDEX.md` first and extend the skill that owns the topic; a new skill is only for a topic no skill owns (KIT-039). Copy [`docs/templates/kit-skill.md`](docs/templates/kit-skill.md) to `plugins/<plugin>/skills/<name>/SKILL.md`; user-only means exactly `triggers: [user]`, Codex `agents/openai.yaml` with implicit invocation disabled, and Claude `disable-model-invocation: true`; run `python3 platforms/tools/gen_index.py` (it copies the description into the plugin's `INDEX.md`) |
| reference | copy [`docs/templates/kit-reference.md`](docs/templates/kit-reference.md) to `plugins/<plugin>/skills/<owner>/references/<topic>.md`; set `kind: fact` with date/sources or `kind: detail`; keep ≤60 lines and link it from `SKILL.md` |
| subagent profile | add `plugins/<plugin>/agents/<name>.md` in the plugin whose skills consume it (reachable through the dependency graph) with frontmatter validated by `platforms/ci/schemas/agent.schema.json`; Devin CLI/Desktop and Claude Code load the profiles, Devin Cloud uses managed Devins and Codex none (README § Platform behavior) |
| template | only for a long artifact a skill links (a spec, a project `AGENTS.md`); a short field list goes inline in the skill. Add `plugins/<plugin>/templates/<prefix>-<name>.md` (prefix `spec`, `doc` or `project`), link it from the skill, then run `python3 platforms/tools/gen_index.py` |
| plugin | create `plugins/<name>/` with `.devin-plugin/plugin.json`, `.claude-plugin/plugin.json`, `plugin.json`, then run `python3 platforms/tools/gen_index.py` for its `INDEX.md`; declare `requiredPlugins`/`dependencies` on the plugins it consumes; register it in the root meta-plugin `requiredPlugins`, `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`. Prefer a skill in `guardrails`: a second plugin is justified only by an audience that must not load `guardrails` (KIT-038, KIT-047). Renaming or removing a plugin adds the old name to the Claude marketplace `renames` map |

A rule uses this frontmatter shape:

```yaml
---
description: <what loads and when, at most 160 characters>
trigger: glob
globs:
  - "<glob>"
  - "<glob>"
---
```

`globs` must be a YAML sequence: Devin rejects a comma-separated string (`YAML parse error: globs: invalid type: string ..., expected a sequence`).

A folder gets a `README.md` only when its files need explanation; shape it with [`docs/templates/kit-readme.md`](docs/templates/kit-readme.md). Outside the generated plugin indexes there is no `INDEX.md` (KIT-042). The `kit-*` templates shape kit content, so they live in `docs/templates/`, outside every plugin.

A subagent skill sets Devin `subagent: true` or a shared `agent: <profile>`, plus Claude `context: fork` and `background: false`; named profiles must exist under `plugins/<plugin>/agents/` of a plugin reachable through the dependency graph.

Hooks are a guard, not a guardrail: they fail open, load only in local Devin and Claude Code, and cannot replace user confirmation or the always-on safety boundaries. The PostToolUse format and lint hook follows the same rule: a missing tool exits 0 with a notice, findings exit 2 with the tool output on stderr, and every branch is covered by `platforms/ci/validations/hook_post_edit_cases.json`, which `check_kit.py` runs with stub tools (timeout ceiling 30 s; the PreToolUse guard keeps 10 s). The guard's one network call, the KIT-020 merged-branch check behind `git branch -D <name>`, fails closed: any `gh` or `git` error or timeout denies, and `platforms/ci/validations/test_hooks_guard_merged_branch.py` covers it with a stub `gh`. The SessionStart synced-folder warning always exits 0 and is covered by `platforms/ci/validations/hook_session_start_cases.json`, which runs on a throwaway `HOME` with a stub `xattr` (timeout ceiling 10 s); its compact branch, the Git state after compaction, is covered by `platforms/ci/validations/test_hooks_guard_compact.py`.

## Third-party skills

Pinned sources live in `platforms/kits/third-party/skills.lock`. Update the SHA, license and verification date, then run:

```bash
platforms/tools/vendor.sh
platforms/tools/vendor.sh --check
```

The command regenerates `plugins/<plugin>/skills/<name>/` and its `VENDOR.md`, where the plugin comes from the lock's second column. MIT and Apache-2.0 require the license text in every copy, so a skill folder without its own `LICENSE*` gets the upstream repository root's, and `--check` fails on a skill without one (KIT-025). Remove a vendor by deleting both its lock line and skill folder.

## CI requirements

- No kit workflow runs on push or pull request (KIT-014): the local gates are the proof, as the PR checklist lists them. A `workflow_dispatch` run is for a check that needs a clean Ubuntu runner.
- `.github/workflows/ci.yml` (`workflow_dispatch`): ShellCheck on tools/kits, `check.sh`, `smoke.sh`, and `check_kit.py --links`.
- Scripts under `platforms/` must parse under bash 3.2 (macOS `/bin/bash`, the `smoke.sh` restricted PATH): avoid unquoted text after a quoted string inside `"$(...)"` — write `"$(basename "$f")"`/`"${f##*/}"` instead of `"$(basename "$f" .md)"` — and an odd number of apostrophes in a heredoc inside `"$(...)"`, a comment's `it's` included. `check_kit.py` § 13 runs `bash -n` on every `*.sh` with the bash on `PATH`, so on macOS it catches what `shellcheck` and the Ubuntu bash 5 accept (KIT-060).
- `check.sh` runs `claude plugin validate` on the plugin and marketplace when Claude Code is installed.
- `check_kit.py` also gates allowed tools, three-way user-only/subagent/rule parity, reference kinds/sources, hooks, backtick paths, links that leave their plugin and a skill description's literal `Use when` and `Not for` (KIT-052), and shell syntax with `bash -n` (KIT-060).
- `check.sh` also runs `gen_index.py --check`: every `plugins/*/INDEX.md` is generated from the plugin's files, so a stale one fails and the message prints `python3 platforms/tools/gen_index.py`. Never edit a plugin `INDEX.md` by hand (KIT-040).
- `.github/workflows/gitleaks.yml` (`workflow_dispatch`): secret scan of the whole history; locally, `gitleaks git --redact --log-opts="origin/main..HEAD"` scans the branch's commits.
- `.github/workflows/evals.yml`: on-demand `claude plugin eval plugins` over the cases of every plugin; needs the `ANTHROPIC_API_KEY` repository secret, which is not set (owner 2026-10-06), so nothing runs it on a schedule.
- `.github/workflows/release.yml`: tag/version validation and release creation.

## Evals

- Cases live in `plugins/<plugin>/evals/<case>/` (`prompt.md` plus `graders/*.md`, `case.yaml` and `fixture.sh` when the case needs a repository); a case without a grader fails to load, and `check_kit.py` rejects a case folder without `prompt.md` or `case.yaml`, or without `graders/*.md`.
- The suite holds one trigger case for each of eight critical skills: `session`, `review`, `git`, `java-standards`, `godot-standards`, `testing`, `protocol-contract` and `code-standards`. A case never names its skill; its `skill-fired` grader checks that the skill fired. Another grader is `tool_used` or `regex` when the output can be matched; an `llm` grader states one PASS and one FAIL line, and a plausible wrong answer meets the FAIL line.
- A change to the `description` of one of those eight skills reruns its case by hand before the PR. A new skill, or a change to another skill, needs no case (KIT-037).
- Locally: `claude plugin eval plugins --case '<name>' --runs 1 --ablation none --no-publish --trust-plugin --output-dir "${TMPDIR:-/tmp}/kit-evals"` (add `--scaffold --allow-tools Bash Edit Write` for cases with a fixture). The target is `plugins`, because a `plugins:` entry loads only from inside the target directory; a case `plugins:` entry outside it fails the case load with "outside the containment root" (KIT-041). `--output-dir` keeps the aggregate result out of `plugins/evals/results/`, which `check_kit.py` would read as a plugin without a manifest. The evals workflow runs only cases tagged `ready`, with a pinned model and judge.
- Before a local run, `claude auth status` must exit 0 (`"loggedIn": true`). Logged out, every case stops before any model turn: the command exits 2 in about a second and the result reads `casesPassed: 0` and `overallScore: 0`, like a skill that fails every grader; only `partialReason: "auth_failed"` and the arm's `error` ("Not logged in · Please run /login") say that nothing ran. A `--scaffold` case also stops, with exit 1, when `~/.docker` holds a symbolic link (Docker Desktop's `~/.docker/bin`), which the Bash sandbox cannot exclude. Record such a case as unverified with that line, never as a failing skill, and rerun it after `claude auth login`.

## KPIs

`platforms/tools/kpi.py <ledger.csv>` prints one line per review-loop batch. The loop's `note` column carries space-separated tokens on `kind=review` rows: `verdict=<approved|flagged|needs-product|needs-human>`, `findings=<n>`, `spec=<n>` (findings owned by `spec`); without them only rounds per PR is available.

- first-pass approval >= 60% (39% on the 33 PRs a consumer project's loop reviewed up to 2026-10-05)
- spec-owned findings <= 25%

After every kit rule change compare two batches, one before and one after, on these numbers: if they do not move, the hypothesis that contradictions cost review rounds is refuted.

## After merging to main

- Devin Cloud needs no manual refresh; it fetches `main` for each session.
- Devin CLI/Desktop re-fetches at app start; run `devin plugins update` to force it.
- Codex and Claude Code refresh through launchd and `platforms/tools/refresh.sh`; run `platforms/tools/doctor.sh` to diagnose local state.
- In Claude Code, use `/doctor prompt-audit` to inspect loaded instructions and `/context` to inspect token cost.
