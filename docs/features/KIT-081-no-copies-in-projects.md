---
id: KIT-081
title: "The kit copies nothing into a project: skills and CI run the kit's own files"
status: confirmed
confirmed: "2026-11-16 (owner, chat of the agent-rules-kit 13.1.0 bundle session, after the platforms/ review: 'Sim, registre')"
issue: "#308"
pr: ""
---

# KIT-081 — The kit copies nothing into a project

## Problem and evidence

The owner's principle, in the platforms/ review: a plugin should hold its files and run them against the project that
uses it, not install copies into that project.

[FACT] Stratics `main` (`git ls-tree -r origin/main`, 2026-11-16) holds 188 files that `platforms/tools/sync-project.sh`
wrote:

| Group | Files | Why it is there today |
|---|---|---|
| `.claude/skills/` and `.claude/ai-kit/` (the pin) | 119 + 35 | KIT-072: Claude Code registers one `ai-kit` marketplace ref per user, and on 2026-11-15 every kit merge changed what each Stratics session loaded, because `refresh.sh` followed `main` |
| `.github/spec-lint/` | 16 | The project's GitHub CI runs on a machine without the kit |
| `.claude/rules/guardrails-*.md` (and the `AGENTS.md` blocks) | 11 | Path rules: Claude Code loads a rule by path from the project's `.claude/rules/`; Codex reads only `AGENTS.md` |
| `kit*.just`, `.github/merge-drivers/` | 4 + 1 | `fmt`/`lint`/`test`/`verify` commands and the keyed-CSV merge driver |
| `.claude/settings.json`, `CLAUDE.md` | 2 | Turn the plugin on for the project; `CLAUDE.md` imports `AGENTS.md` |

[FACT] Each kit release needs a project PR that rewrites those copies (#299: the Stratics re-pin after 13.1.0).
`sync-project.sh` is 1,056 lines and its helpers `sync_pinned_plugin.py`, `sync_agents_md.py` and `sync_just.py` another
1,027 (`wc -l`), and 8 test modules name `.github/spec-lint/` alone (`git grep -l spec-lint -- platforms/ci/validations/test_*.py`).

[FACT] What changed since KIT-072: from 13.1.0 (#271) the `~/.ai-kit` clone and the Codex marketplace follow the newest
`vX.Y.Z` release tag. The kit repository is public (`gh repo view --json visibility`), so a project's CI can fetch it at a
tag without a token.

[FACT] Claude Code does not follow the release yet: on 2026-11-16 the user-scope `guardrails@ai-kit` record in
`~/.claude/plugins/installed_plugins.json` was at `a008d72` (`main` after #304), while `~/.ai-kit` was at `v13.1.0`
(`5a4924e`). KIT-080 left it on `main` (#271): Claude Code 2.1.287 takes a marketplace ref (`owner/repo#ref`) but has no
command that changes it, a second add with another ref is refused while the first source is declared, and
`claude plugin marketplace remove` uninstalls the plugin and deletes its data (the rule-load log).

## Change

The project keeps configuration only: `.claude/settings.json` (the plugin is on), `CLAUDE.md`, and the CI lines that
name the kit release. Every check runs from the kit's own files. Three stages, one PR each, every stage with its
migration line for consumer projects:

1. **Spec tools from the kit.** Skills, the post-edit hook and the `docs` just module call
   `~/.ai-kit/platforms/ci/validations/` (`check_spec.py`, `row_checks.py`, `spec_trace.py`,
   `check_docs_structure.py`) with `~/.ai-kit/platforms/ci/schemas/`, not `.github/spec-lint/`. The project's CI runs the
   same tools through a composite action the kit publishes, whose scripts and schemas come with the pinned commit
   (`github.action_path`), referenced as `uses: ChristianPrzybulinski/agent-rules-kit/<action>@<40-character SHA> #
   vX.Y.Z`; Renovate or Dependabot bumps that line when the kit releases and merges it on green CI (option B below,
   owner decision 2026-11-16). The `spec-lint.yml` and `pr-contract.yml` templates call the action. `sync-project.sh` stops
   writing `.github/spec-lint/`, and `--check` stops comparing it.
2. **No pin.** The vendored mode (`--vendor-skills`, `.claude/skills/` copies, `.claude/ai-kit/`,
   `guardrails-pinned`) goes; the project turns on `guardrails@ai-kit`, which follows the release the machine installed.
   Prerequisite: Claude Code follows the release. Without it, ending the pin brings back the KIT-072 problem, each kit
   merge changing every project session. Proposed: a `stable` branch that the release workflow moves to each release
   tag; the Claude and Codex marketplaces (and the project's `extraKnownMarketplaces`) name `#stable` once, so a release
   reaches them through a plain `marketplace update` and no project file changes per release. The one-time move per
   machine backs up the plugin data folder before the remove and restores it after the add.
3. **Path rules without copies.** A plugin hook gives the agent the rule when it reads or edits a file the rule's globs
   match, as the `git` hook already adds context to a commit; `.claude/rules/` copies and the `AGENTS.md` blocks go once
   it is measured.

### How a project's CI gets the kit (review of 2026-11-16, option B chosen)

A web review of primary sources compared five ways to run shared validators in many repositories' CI:

| Option | Verdict |
|---|---|
| A. Copy into the project (today) | Hermetic, but one sync PR per release and copies that drift; Google's monorepo model |
| **B. Reference pinned to a commit, bumped by a bot on release** | Recommended by GitHub ("the safest option for stability and security" for reusable workflows), GitLab and Azure; hash-pinned users were unaffected by the tj-actions tag rewrite (CVE-2025-30066) |
| C. Floating ref (`stable`, `main`) | Weakest: a bad or compromised release reaches every consumer at once; Scorecard counts it as unpinned; pre-commit refuses a branch as `rev` |
| D. Published package | Strong when pinned by hash; needs a publishing pipeline |
| E. Agent skill only, no CI check | Rejected by the vendors as a gate |

The vendors' own docs on E:
- Claude Code: a rule that must hold every time goes into a hook. Claude Code Review "never approves or blocks".
- OpenAI: Codex review is "an additional reviewer", and tests and branch protections provide the hard enforcement.
- Copilot: its review "may not identify all of the problems".

So the skill runs the same validator early, and CI is the gate.

What proves B wrong:
- Over 4 weeks, the bump PRs need the owner more than about once a week (required reviews block automerge).
- The bumps often break the consumer's CI, which would make kit compatibility the problem rather than distribution.

The machine install keeps `stable` (option C) because the kit is first-party, only the release workflow moves it, after
a green `ci-full`, and Claude Code has no other way to follow releases. Recommended alongside it: GitHub immutable
releases on the kit (owner setting).

Sources:
- https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows
- https://docs.github.com/en/actions/reference/security/secure-use
- https://github.com/ossf/scorecard/blob/main/docs/checks.md
- https://www.cisa.gov/news-events/alerts/2025/03/18/supply-chain-compromise-third-party-github-action-cve-2025-30066
- https://pre-commit.com/
- https://docs.renovatebot.com/key-concepts/automerge/
- https://code.claude.com/docs/en/hooks-guide
- https://code.claude.com/docs/en/code-review
- https://developers.openai.com/blog/custom-code-review-rules-for-codex
- https://docs.github.com/en/copilot/responsible-use/code-review
- https://github.blog/changelog/2025-10-28-immutable-releases-are-now-generally-available/

The starter files a new project needs (`.gitignore`, `.gdlintrc`, the PR template) are the project's own: a skill writes
them once from the kit templates when it sets the project up; no sync script copies them.

**Stage 2a, the prerequisite of stage 2: every install follows `stable`.** `release.yml` moves the `stable` branch to
the released commit as its last step, after `gh release create`, through the API and fast-forward only (`gh api -X PATCH
repos/<repo>/git/refs/heads/stable -f sha=<commit> -F force=false`). `bootstrap.sh` adds Claude Code's marketplace as
`ChristianPrzybulinski/agent-rules-kit#stable` and Codex's with `--ref stable`; `kit-release.sh` holds the branch name
(`KIT_STABLE_BRANCH`) and reads Claude Code's ref (`claude_kit_ref`, from `known_marketplaces.json`). `refresh.sh` moves
each marketplace that follows another ref once: Codex by a remove and an add (as #271 did per tag), Claude Code by
copying each kit plugin's data folder to `${XDG_STATE_HOME:-~/.local/state}/ai-kit/plugin-data-backup/<UTC time>/`,
`claude plugin marketplace remove ai-kit --scope user`, an add at `#stable`, `claude plugin install <plugin>@ai-kit
--scope user` and a restore (a file the reinstall wrote stays; a `.jsonl` both hold keeps the backup's lines first,
under the hook's lock); the backup stays, and a failure names the commands left. From then on a release arrives through
`claude plugin marketplace update` and `codex plugin marketplace upgrade`. `doctor.sh` fails while Claude Code's or
Codex's marketplace or Devin's team plugin follows another ref; it moves Codex itself and, for Claude Code, names
`refresh.sh`, which backs the data up first. `sync-project.sh` writes the project's `extraKnownMarketplaces.ai-kit`
source with `"ref": "stable"`, and `--check` reports one without it. The `--scope user` on the remove is this stage's
own: without a scope Claude Code 2.1.287 removes the declaration "from every scope" (`claude plugin marketplace remove
--help`), so a run inside a repository could edit that project's tracked `.claude/settings.json` (`[HYPOTHESIS]`,
not probed).

**Stage 2b, no pin.** The vendored mode goes: `sync-project.sh --vendor-skills` exits 2 with a line naming this stage,
and `platforms/tools/sync_pinned_plugin.py` (pin, write, rewrite, settings and check) with it; the project enables
`guardrails@ai-kit`, which follows `stable` since stage 2a. A repository that still holds the vendored state is
migrated by the plain sync through `platforms/tools/sync_unvendor.py`, which keeps the safe part of the old `remove`:
after the plugin is on and `CLAUDE.md` records the profile list, it deletes `.claude/skills/KIT_MANIFEST.json`, each
`.claude/skills/<name>/` and `.claude/ai-kit/` that carries the `.agent-rules-kit` marker, and in `.claude/settings.json`
the hook handlers that run `.claude/ai-kit/hooks/` and the `guardrails-pinned@skills-dir` key, one line per removal; an
unmarked folder or a symbolic link is never read, replaced or deleted, and nothing is read through a symbolic `.claude`
or `.claude/skills`. `--check` fails on each leftover, naming it and the sync. The profile list moves from
`KIT_MANIFEST.json` to the generated `CLAUDE.md` marker (`<!-- generated by agent-rules-kit sync-project.sh v<version>;
profile <list>; AGENTS.md is the source -->`): `--profile`, else the marker, else the manifest (the migration), else
inference, and `--check` reports a marker whose list differs from the one in effect. `doctor.sh` drops the KIT-072
checks (the head beside vendored copies, trust for pinned roots) and warns about each checkout with an `@ai-kit` install
record that still holds the vendored state, naming `sync-project.sh <repo>`. The rules and the `AGENTS.md` blocks name
`~/.ai-kit/plugins/guardrails/skills/<skill>/` as the only home of a kit skill. Removing a flag of a shipped tool and
the project destinations it wrote is a breaking change, so the release that carries it is MAJOR.

**Stage 1, the spec tools.** The composite action `platforms/ci/actions/spec-tools/action.yml` runs the validators
and schemas from its own checkout (`$GITHUB_ACTION_PATH/../../validations/`, `../../schemas`), never a fetch of another
ref. Its input `checks` (default `spec`) takes `spec` (`check_spec.py`, `check_docs_structure.py`, which passes as
`off` unless `sdd.doc_structure.enabled`, and on a pull request the baseline that may only shrink), `trace`
(`spec_trace.py check`), `rows` (`row_checks.py check`, `--changed` on a pull request, `--all` otherwise) or `none`;
`base` and `head` default to the pull request's commits. It sets up Python 3.12 with `actions/setup-python` pinned by
SHA, installs `pyyaml` and `jsonschema`, and exports `AI_KIT_DIR`, the kit root at the pinned commit, to
`$GITHUB_ENV` (zizmor's `github-env` finding is silenced there as a documented false positive: a fixed name and the
action's own path). The `spec-lint.yml` template calls it with `checks: spec`, and its `paths` include the workflow
itself, so a bot's pin bump runs the check it updates; `pr-contract.yml` calls it with `checks: none` and runs
`"$AI_KIT_DIR/platforms/ci/validations/pr_gates.py"`, so its `script` input is gone and `config` defaults to
`.github/pr-gates.json`. The template carries a real release pin (`v13.1.0`), which zizmor's online audits accept and
the kit's Dependabot moves to each release (`.github/dependabot.yml` also watches the action's folder); that release
predates the action, so a project takes the file from the sync until a release ships it. Sessions run the installed
kit: the skills name `~/.ai-kit/platforms/ci/validations/<tool>` with `~/.ai-kit/platforms/ci/schemas`, and the
post-edit hook and `docs.just` read `${AI_KIT_DIR:-$HOME/.ai-kit}`. `sync-project.sh` stops writing
`.github/spec-lint/` and `KIT_VERSION` (`platforms/tools/sync_spec_tools.py`): install removes a generated copy, only
when its `README.md` starts with the generated heading and only the kit-named files (validators, schemas,
`KIT_VERSION`, the README, the validators' byte caches), keeps any other file with a `sync: kept` line, never follows
a symbolic link, and warns about each workflow line that still names the copy; in a repository with `docs/spec` whose
CI runs no spec tools it writes `spec-lint.yml` (or the `--workflow` name) when that file is missing, the action pinned
to `git rev-parse HEAD` of the kit with `# v<VERSION>`, and warns when that commit is not the release tag. A workflow
runs the spec tools when a line that is not a comment uses the action or runs `check_spec.py` from `$AI_KIT_DIR`.
`--check` fails on a generated copy left, on each workflow line naming `.github/spec-lint/` (`file:line` and the fix)
and, with `docs/spec`, on no workflow that runs the spec tools. `check_docs_structure.py` no longer exempts
`.github/spec-lint`, since the kit stops generating it. Out of this stage: the `kit*.just` modules, the merge driver
and `.claude/rules` (stage 3).

Open before stage 2 and 3 (each `[HYPOTHESIS]` until checked against the installed version or its docs):

- A Claude Code plugin cannot ship path-scoped rules (stage 3 rests on it).
- Codex has no way to receive a path rule without a file in the project (stage 3 keeps the `AGENTS.md` block for Codex
  if so).
- No consumer needs a kit version other than the machine's for longer than a release cycle (stage 2 rests on it).
- ~~A marketplace declared `owner/repo#stable` updates to the branch's new commit on `claude plugin marketplace update`
  and `codex plugin marketplace upgrade` (the stage 2 prerequisite rests on it).~~ Checked on 2026-11-16, below.

[FACT] Probe in a throwaway `HOME` (2026-11-16, Claude Code 2.1.287 and the Codex CLI on the owner's Mac):
`claude plugin marketplace add "ChristianPrzybulinski/agent-rules-kit#<branch>"` and `codex plugin marketplace add
ChristianPrzybulinski/agent-rules-kit --ref <branch>` both clone the branch; after a new commit was pushed to it,
`claude plugin marketplace update ai-kit` and `codex plugin marketplace upgrade ai-kit` both moved to that commit. A
branch ref follows its branch; a tag ref would need a remove and an add per release.

[FACT] Claude Code 2.1.287 in a throwaway `HOME` and `CLAUDE_CONFIG_DIR` (2026-11-16): the add at `#stable` records
`{"source": "github", "repo": ..., "ref": "stable"}` in `plugins/known_marketplaces.json` and in the user
`settings.json` `extraKnownMarketplaces`; `claude plugin marketplace remove ai-kit --scope user` reports "Also
uninstalled 1 plugin" and deletes `plugins/data/guardrails-ai-kit/`; the add and install that follow put
`guardrails@ai-kit` back at `5a4924e` (`stable`, = `v13.1.0`) without creating the data folder; with
`CLAUDE_CODE_PLUGIN_CACHE_DIR` set, `known_marketplaces.json` is written there instead.

What proves the change wrong: a consumer that must stay on an older kit release while the machine moves on, or a
hook-delivered rule followed less often than the path rule (measured as in KIT-070).

## Proof

Per stage: `bash platforms/tools/check.sh`, `python3 platforms/tools/run_tests.py --start platforms/ci/validations
--changed-from origin/main`, the consumer fixture (`test_consumer_fixture.py` in `ci-full.yml`) passing with no
`.github/spec-lint/` in the project, and `git grep -n 'spec-lint/' -- plugins platforms/kits` printing nothing after
stage 1.

## History

- 2026-11-16: confirmed (owner). Replaces the unrecorded starter-file proposal of the same session (a sync step that
  wrote starter files into a project).
- 2026-11-16: the owner chose stage 2 first, and agreed on the `stable` branch as its prerequisite; the CI side of stage 1
  waits for a best-practices review (vendored copy, pinned reference or agent-only check).
- 2026-11-16: stage 2a (every install follows `stable`, above) implemented on `feat/kit-081-stable`; the `stable`
  branch exists at `5a4924e` (= `v13.1.0`). Each machine moves once on its next `refresh.sh`; Devin's team plugin ref
  is set to `stable` by hand once.
- 2026-11-16: the owner chose option B for the project's CI ("Sim, registre o B").
- 2026-11-16: stage 2b (no pin) implemented on `feat/kit-081-no-pin`, on top of stage 2a, owner-approved ("Sim, comece
  pelo pin", "implemente tudo isso agora"); a dry migration of a copy of the Stratics vendored state is in the PR.
- 2026-11-16: stage 1, the spec tools (option B), implemented on `feat/kit-081-spec-tools`, on top of stage 2b,
  owner-approved ("implemente tudo isso agora"); a dry migration of a copy of Stratics is in the PR.
- 2026-11-16: [FACT] probe in a throwaway home (Claude Code 2.1.287), set up with a user-scope and a project-scope
  `guardrails@ai-kit` install on a ref-less marketplace.
  - `claude plugin marketplace remove ai-kit --scope user`, `add ...#stable` and `install --scope user` kept both
    install records.
  - `claude plugin list` in the project still listed the project entry, enabled, and the project's
    `.claude/settings.json` was untouched. So the stage 2a move leaves a project's records in place.
  - The cache directory is named by version (`13.1.0`), so right after the move it still held the files installed from
    `main`. `refresh.sh`'s KIT-013 reinstall (a user-scope cache that differs from the marketplace clone, now on
    `stable`) corrects it on the next run.
