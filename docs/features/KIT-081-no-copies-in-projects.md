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

**Stage 1b, the `just` modules and the merge driver.** [FACT] just 1.58.0 (`just --changelog`; just.systems/man/en
imports, modules and strings pages; probed in a throwaway `HOME` on 2026-11-16): an `import` or `mod` path may be
absolute and "A leading `~/`" in it "is replaced with the current user's home directory"; it is a string, not an
expression (`import env('HOME') + '...'` is a parse error); an imported recipe runs in the importing justfile's folder,
also inside a submodule; a `mod` module's recipes run "with the working directory set to the directory containing the
submodule source file" unless `[no-cd]`, which gives the invocation folder; `import?` is optional. A shell-expanded
`x'${AI_KIT_DIR:-~/.ai-kit}/...'` path also resolves, but `${VAR:-DEFAULT}` keeps a set-but-empty variable and `~` in
the default is not documented, so the line names `~/.ai-kit`. So each profile folder's justfile holds
`import '~/.ai-kit/platforms/kits/just/<profile>.just'`, the one line `platforms/tools/sync_just.py` writes: into a
starter justfile, or in place of an `import 'kit.just'` line whose `kit.just` was generated (and of another profile's
kit import after a profile switch). A folder with several profiles gets no import and a warning: a `mod` module would
run its recipes in the kit's folder, and two imports define the same recipe names. The spec-tools action links
`$HOME/.ai-kit` to its own checkout unless a kit is there (then it warns), and the `ci-godot.yml` and `ci-java.yml`
templates call it with `checks: none` before their first `just` step. The keyed-CSV merge driver is not copied: the
printed `git config merge.keyed-csv.driver` line runs `python3 ~/.ai-kit/platforms/kits/godot/scripts/keyed_csv_merge.py`
(git runs it through `sh`, which expands `~`), and `.gitattributes` stays the project's. Migration: install removes a
`kit.just` or `kit-<profile>.just` whose first line carries the generated marker and the driver whose second line is the
kit's docstring, keeps an unmarked one (`sync: kept`) and never reads or removes through a symbolic link; `--check`
fails on each marked copy left, on a justfile line that imports the removed `kit.just` (`file:line` and the fix), on a
single-profile folder whose justfile lacks the import, and on a `merge.keyed-csv.driver` config that still runs the
removed copy (read with `git config --get`, never written). `check_docs_structure.py` no longer exempts
`.github/merge-drivers`.

**Stage 3, path rules from the plugin (Claude Code).** Claude Code loads a path rule by itself only from a project's
`.claude/rules/`, so `sync-project.sh` rendered each rule the profile receives into `.claude/rules/<plugin>-<rule>.md`.
The `guardrails` plugin now gives the rule: `plugins/guardrails/hooks/path_rules.py`, a PostToolUse hook with the matcher
`^(Read|Edit|Write|MultiEdit|NotebookEdit|Bash|Grep)$`, run as `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/path_rules.py" ||
exit 0` with a 5 s timeout.

- Gate: the project root is `$CLAUDE_PROJECT_DIR`, else the event's `cwd`; the hook acts only when line 1 of that
  root's `CLAUDE.md` is the sync marker (`<!-- generated by agent-rules-kit sync-project.sh v<version>; profile
  <list>; AGENTS.md is the source -->`). The plugin is enabled at user scope everywhere, so any other repository gets
  nothing.
- Profiles: the profile names of the marker's list (`docs,godot:client,java:server` gives docs, godot and java) select
  the rules through the profile map, as they selected the copies. The map moved from `platforms/tools/sync-profiles.txt`
  to `plugins/guardrails/hooks/sync-profiles.txt`, next to the hook: [FACT] the install holds only the plugin folder
  (`~/.claude/plugins/cache/ai-kit/guardrails/<version>/`, listed on 2026-11-16), so
  `${CLAUDE_PLUGIN_ROOT}/../../platforms/tools/` does not exist there, and the map now ships with the rules it selects.
  `sync-project.sh` reads it from the plugin folder for the `AGENTS.md` blocks.
- Match: the candidates are `tool_input` `file_path`, `notebook_path` and `path`, and for Bash the path-like words of
  the command (shlex, quotes removed, operators split off; an option's value after `=`; a trailing `:line[:col]` cut;
  a word with `/` or `.`, never a variable, a URL or bare dots; at most 256 words). Each is made relative to the root,
  and one that resolves outside it is also matched as written. A glob supports `**/` (which may be empty), `**`, `*`
  and `?`, the forms the kit rules use. The globs are the kit's own: the `<profile>:<dir>` and `sdd.rule_paths` scopes
  only narrowed the copies, so the hook gives a superset of what they gave (a `.py` outside the profile folders gets
  the code rule), and reading `sdd.rule_paths` would need `check_spec.py` on every call. The scopes still shape the
  `AGENTS.md` blocks.
- Once per session: the rule names given are kept in `${CLAUDE_PLUGIN_DATA}/path-rules/<session_id>.json` under an
  `flock`, so parallel tool calls give a rule once; a session's first file prunes the files older than 3 days. Without
  `CLAUDE_PLUGIN_DATA` the hook gives nothing, since the promise cannot hold.
- Output: `hookSpecificOutput.additionalContext`, one block per rule that names it, its globs, the file that triggered
  it and where the kit files it names are (`<plugin folder>/skills/<skill>/references/<file>`, the line the copies
  carried under their marker), then the body without frontmatter.
- Log: each delivery appends one record to the rule-load log the InstructionsLoaded hook writes
  (`${CLAUDE_PLUGIN_DATA}/instructions-loaded.jsonl`, same fields, lock and 5 MiB rotation) with `load_reason`
  `kit_hook_path_match` and the plugin's `rules/<rule>.md` as `file_path`; `skill_usage.py --rules` counts it under the
  rule.
- Failure: any error exits 0 with nothing on stdout, and the command's `|| exit 0` covers a missing interpreter or
  script, so the hook never blocks a tool.
- Not added to the matcher: Devin's lowercase tool names, which the guard and lint hooks also name. Devin CLI loads
  the kit rules by `globs` itself (README, Platform behavior), so the hook would give each rule twice there, and
  `codex features list` on codex-cli 0.164.0 says `plugin_hooks removed`.
- [FACT] Runtime, 2026-11-16, system Python 3.9.6 on the owner's arm64 Mac, a project synced with the godot profile,
  20 runs of the `hooks.json` command each: median 94 ms for a call that gives two rules (p90 186 ms), 94 ms for a Bash
  call whose rules were given (p90 226 ms), 82 ms for a file no rule matches and 79 ms in a repository without the
  marker, against 69 ms for `bash -c 'python3 -c pass'` alone; the interpreter start is most of it.
  `test_hooks_path_rules.py` holds it under 0.5 s (performance layer).

`sync-project.sh` stops writing `.claude/rules/`. `platforms/tools/sync_rules.py` migrates a synced repository: after
the sync has written the `CLAUDE.md` marker the hook needs, it removes each `.claude/rules/*.md` that is a regular file
with a line starting `<!-- agent-rules-kit: generated from ` (every name the kit used: `guardrails-`, `core-`, `dev-`,
`sdd-`), one `sync: removed` line each, names every other entry with a `sync: kept` line, removes the folder when it
is left empty, and reads nothing through a symbolic `.claude` or `.claude/rules`; the refusal of an unmarked file
under a kit copy's name goes, since the sync writes nothing there. `--check` fails on each kit-marked copy left,
naming it and the sync. The summary line names the hook instead of a copy count. The rendered rule that feeds an
`AGENTS.md` block loses the kit-files line, which only the copies carried, and the block intro says Claude Code
receives the same rules from the plugin's hook. The `AGENTS.md` blocks stay: Codex reads only `AGENTS.md`, and
stage 3 for Codex waits for a Codex probe. The five `rule` eval cases write the `CLAUDE.md` marker with a profile that
selects their rule and copy no rule, so they measure the hook; they were not run (the Docker store, CONTRIBUTING §
Evals). Removing a project destination makes the next release MAJOR.

**Stage 3 for Codex, part 2: edits (`apply_patch`).** [FACT] Codex probe of 2026-11-19 (codex-cli 0.164.0, #308
comment): a plugin's `hooks/hooks.json` hook fires on tool use once trusted and its `additionalContext` reaches the
model, and a file edit is an `apply_patch` call whose input is `{"tool_name":"apply_patch","tool_input":{"command":
"*** Begin Patch\n*** Add File: <abs path>\n..."}}`, with no `file_path`, `notebook_path` or `path`; the probe's
`apply_patch` arm fired Pre and Post. Codex reads files through Bash (`cat`, `sed`, `rg`), which the hook already
handles.

Scope (this part only; the manifest fix and the trust record are other parts, and the `AGENTS.md` blocks stay until
both land):
- `plugins/guardrails/hooks/path_rules.py`: for `tool_name == "apply_patch"`, `candidates()` adds the path of each
  `*** Add File:`, `*** Update File:`, `*** Delete File:` and `*** Move to:` header (`patch_paths()`). A header counts
  only at the start of a line: the format starts every body line with `+`, `-`, a space or `@@`, so a body line that
  looks like a header (`+*** Update File: x`) is not a file. Bounded: the first 1 MiB (`MAX_PATCH_CHARS`), 64 paths
  (`MAX_PATCH_PATHS`), a path of at most 4096 characters. The rest is the Claude Code behavior: the root gate, the
  profile map, once per session, the log record, exit 0 and nothing on stdout on any error.
- `hooks.json` is unchanged: [FACT] the Codex hooks doc matches `apply_patch` through the `Edit` and `Write` aliases
  of the existing matcher, and the probe saw the hook fire for it. Not probed: a matcher that names only `apply_patch`.
- `platforms/ci/validations/test_hooks_path_rules.py` (`ApplyPatchTest` and one `HookCommandTest` case),
  `plugins/guardrails/hooks/README.md` and the `CHANGELOG.md` line.

Not verified: a real Codex `apply_patch` event through the hook (the tests feed the probe's captured JSON shape); a
Codex `apply_patch` whose paths are relative to a `cwd` other than the project root beyond what `match_forms` does for
every tool; the other patch spellings a later Codex release may add (a header the parser does not know gives no path,
so no rule, never an error).

### Stage 3 measurement (2026-11-16, before the owner's go-ahead)

Method: Claude Code 2.1.287, Opus 5.5, `claude -p` in throwaway project folders. The five `rule` eval cases of
`plugins/guardrails/evals/*-rule-*` ran 5 times in each of three arms: A, the rule copied in `.claude/rules/` as the
sync did; B, no copy, the rule given by a PostToolUse hook from a test plugin loaded with `--plugin-dir`; C, no rule
at all. Each case's own graders scored the runs: regex for most, a haiku judge for the two `llm` graders.

| Case | A copy | B hook v1 | C none | B2 hook v2 |
|---|---|---|---|---|
| code-rule-one-decision-one-place | 5/5 | 4/5 | 0/5 | 5/5 |
| godot-rule-boot-exit-code | 5/5 | 5/5 | 1/5 | 5/5 |
| protocol-rule-required-field-bumps-version | 5/5 | 4/5 | 3/5 | 5/5 |
| java-rule-constructor-injection | 5/5 | 5/5 | 5/5 | — |
| tests-rule-empty-return-passes | 5/5 | 5/5 | 5/5 | — |

- java and tests pass with no rule, so they do not discriminate.
- B, hook v1: the matcher was Read, Edit, Write and MultiEdit. It fired in 22 of 25 runs, and all 22 passed. The other
  3 runs read the files only through Bash (`cat`, `cat -n $f` in a loop), so v1 never fired; 2 of those 3 failed.
- B2, hook v2: adds Bash and Grep and takes the path-like words of a Bash command. It fired in all 15 runs and scored
  15/15, equal to A.
- How A delivered its rule: Claude Code's own path-rule load (`InstructionsLoaded`, `path_glob_match`) happened in only
  6 of 25 runs; in 17 the agent found `.claude/rules/guardrails-*.md` in the tree and opened it itself.
- Cost: $21.44 in total. Not measured: other models, and Codex.

[FACT] End-to-end proof, 2026-11-16: `sync-project.sh --profile godot` on a throwaway Godot project wrote no
`.claude/rules`; in it, `claude -p "Read main.gd and tell me which kit rule applies" --output-format json --max-turns 4
--allowedTools Read --plugin-dir <worktree>/plugins/guardrails` (Claude Code 2.1.287) answered with the `godot` and
`code` rules and their globs, and the plugin's log holds two `kit_hook_path_match` records for that session
(`rules/code.md`, `rules/godot.md`, trigger `main.gd`); $0.44. With `--plugin-dir`, only the `guardrails-inline` data
folder logged that session, so the directory copy took the place of the user-scope `guardrails@ai-kit` for it, with no
error.

### Stage 3 for Codex, part 1: the plugin manifest (2026-11-19, #308)

[FACT] Codex probe on codex-cli 0.164.0 (issue #308, comment of 2026-11-19): `codex features list` says `plugin_hooks
removed`, which is a vestigial flag; a hook shipped in a plugin's `hooks/hooks.json` fires and its `additionalContext`
reaches the model once the hook is trusted. The kit's own plugin listed **zero** hooks, with no warning or error.

[FACT] Isolated 2026-11-19 with `hooks/list` of `codex app-server` in a throwaway `CODEX_HOME`, each arm a copy of
`plugins/guardrails` installed with `codex plugin add guardrails@ai-kit` from a local marketplace that mirrors
`.agents/plugins/marketplace.json`:

| Arm | Root `plugin.json` | `.claude-plugin/` | Hooks listed |
|---|---|---|---|
| a, as shipped | `$schema` = agent-plugins.org | kept | 0 |
| b | no `$schema` | kept | 8 (2 PreToolUse, 2 PostToolUse, 3 SessionStart, 1 SubagentStart) |
| c | `$schema` = agent-plugins.org | removed | 0 |
| d | no `$schema` | removed | 8 |
| e, f, g | an unknown key, a `$schema` naming `https://example.com/x.json`, an `author` object | kept | 8 each |
| h, i | `$schema` = agent-plugins.org, first or last key | kept | 0 each |
| m | no `$schema`, `"hooks": "./hooks/hooks.json"` | kept | 8 |
| l | agent-plugins.org `$schema` and `"hooks": "./hooks/hooks.json"` | kept | 0 |

So the cause is the `$schema` value `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`, not the key, its
position or the manifest lookup order (`.claude-plugin/plugin.json` ahead of the root file). The binary holds that URL
beside "Agent Plugins manifest" error strings, so a manifest naming it is read as an Agent Plugins manifest, whose hooks
a `hooks/hooks.json` does not supply (`[HYPOTHESIS]` for the mechanism; the arms show the effect). Skills load either
way (23 with and without it, `skills/list`). Nothing in the kit read the key: the Claude Code and Devin manifests are
their own files, and `bump_version.py` and `kit-release.sh` replace only the `"version"` field.

Scope: `plugins/guardrails/plugin.json` loses its `$schema` line; `check_kit.py` fails a `$schema` key in any plugin's
root manifest (all values: a schema URL of another site worked, but the kit has no use for one); the tests are
`platforms/ci/validations/test_check_kit_manifests.py`. Not in this part: the trust record per user and release, the
path-rule hook's `apply_patch` input and the removal of the `AGENTS.md` blocks (the rest of stage 3 for Codex).

| ID | Given | When | Then | Proof |
|---|---|---|---|---|
| CA-1 | the kit's plugin manifests | `check_kit.py` runs | each root `plugin.json` has no `$schema`; one that has fails with the file and the consequence | `python3 platforms/tools/run_tests.py platforms/ci/validations/test_check_kit_manifests.py` |
| CA-2 | a copy of `plugins/guardrails` installed in a throwaway `CODEX_HOME` | `hooks/list` runs | it lists 8 hooks | the probe harness of the History line; not a CI test, since CI has no Codex |

Migration: Codex skips an untrusted hook without any message, so after the fix the plugin's hooks are listed but do not
run until the user trusts them (`/hooks` review, or `[hooks.state."<key>"]` in `config.toml` with the `trusted_hash`
and `trusted_content_hash` that `hooks/list` returns). A kit release that changes a hook needs a new review. Hooks that
now run in Codex are the ones in `hooks/hooks.json`: guard, lint, git context, path rules and session start.

Open before stage 2 and 3 (each `[HYPOTHESIS]` until checked against the installed version or its docs):

- ~~A Claude Code plugin cannot ship path-scoped rules (stage 3 rests on it).~~ A plugin hook gives them instead;
  measured for stage 3 above.
- Codex has no way to receive a path rule without a file in the project (stage 3 keeps the `AGENTS.md` block for Codex
  if so). Probed 2026-11-19: Codex does run a plugin's hooks once trusted, and the kit's plugin listed none because of
  its `$schema` (part 1 above); open still: the trust record, `apply_patch` input and the removal of the blocks.
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
hook-delivered rule followed less often than the path rule (measured as in KIT-070; for stage 3, the table above, where
the hook matched the copy on Opus 5.5).

## Proof

Per stage: `bash platforms/tools/check.sh`, `python3 platforms/tools/run_tests.py --start platforms/ci/validations
--changed-from origin/main`, the consumer fixture (`test_consumer_fixture.py` in `ci-full.yml`) passing with no
`.github/spec-lint/` in the project, and `git grep -n 'spec-lint/' -- plugins platforms/kits` printing nothing after
stage 1.

| ID | Given | When | Then | Proof |
|---|---|---|---|---|
| CA-1 | a synced project whose stacks select the `code` and `godot` rules | the hook reads an `apply_patch` event whose patch holds an `*** Add File:`, `*** Update File:`, `*** Delete File:` or `*** Move to:` header for `src/a.gd` (absolute or project-relative; one of several files; the source or the destination of a move) | it gives `code` and `godot` once per session, with the log record and the trigger file of the header; a patch whose paths match no rule, a body line that looks like a header (`+*** Update File: src/a.gd`, a context line, `*** End Patch`), another tool with a patch-like `command`, and a malformed or oversized patch (past 1 MiB or 64 paths) give nothing and exit 0 | `python3 platforms/tools/run_tests.py platforms/ci/validations/test_hooks_path_rules.py` |

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
- 2026-11-16: stage 1b, the `just` modules and the merge driver from the installed kit, implemented on
  `feat/kit-081-just`, on top of stage 1, owner-approved ("implemente tudo isso agora"); a dry migration of a copy of
  Stratics is in the PR.
- 2026-11-16: stage 3 measured (above) and approved by the owner ("Sim, implemente"); implemented for Claude Code on
  `feat/kit-081-stage3-rules-hook`: the plugin's path-rule hook, the profile map beside it, no `.claude/rules` copy and
  its migration (`sync_rules.py`), and the rule eval fixtures on the hook. Open: stage 3 for Codex and the removal of
  the `AGENTS.md` blocks, both waiting for a Codex probe.
- 2026-11-19: stage 3 for Codex, part 1 (branch `fix/codex-plugin-manifest`): Codex probe (#308) found 0 hooks listed for
  the kit's plugin; isolated to the root `plugin.json` `$schema` value (agent-plugins.org), removed, and `check_kit.py`
  fails it. Probe harness (throwaway `CODEX_HOME`, `hooks/list` over `codex app-server`) kept in the session scratchpad,
  not in the repo. Open: trust record, `apply_patch` input for `path_rules.py`, the `AGENTS.md` blocks.
- 2026-11-19: Codex probe (#308 comment): plugin hooks fire in codex-cli 0.164.0 once trusted, and a Codex file edit
  is an `apply_patch` call with the patch text only. Stage 3 for Codex part 2 (edits): `path_rules.py` reads the
  headers of an `apply_patch` patch (above, CA-1). Open: the per-user hook trust record, then the removal of the
  `AGENTS.md` blocks.
