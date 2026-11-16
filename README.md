# agent-rules-kit

Shared rules, skills and guard hooks for AI coding agents: Devin Cloud, Devin CLI/Desktop, Codex and Claude Code load the same always-on rules and the same skills from one install. One person maintains the kit for their own work (Java 25, Godot 4 with GDScript, Python and a spec-driven workflow), so its defaults follow those stacks; anyone may use or fork it under the [MIT license](LICENSE).

Issues are welcome: a bug, a question or a proposal for a rule or skill ([new issue](https://github.com/ChristianPrzybulinski/agent-rules-kit/issues/new/choose)). Open a pull request only after its issue exists and the maintainer has agreed to the change there, as [`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md#outside-contributors) says. Answers come as time allows; there is no support commitment. Report a vulnerability privately, as [`.github/SECURITY.md`](.github/SECURITY.md) says, never in an issue. Everyone taking part follows the [code of conduct](.github/CODE_OF_CONDUCT.md).

A plugin-first source of always-on rules, triggered rules, skills, references and templates for Devin Cloud, Devin CLI/Desktop, Codex and Claude Code. Plugin content lives under [`plugins/`](plugins/) — one plugin, `guardrails`, with shared manifests (KIT-047, renamed from `core` by KIT-055); tooling and documentation stay at repository root.

Version: [`VERSION`](VERSION) · History: [`CHANGELOG.md`](CHANGELOG.md) · Contributing: [`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md) · Security: [`.github/SECURITY.md`](.github/SECURITY.md)

## Layout

| Path | Purpose |
|---|---|
| [`plugins/guardrails/`](plugins/guardrails/INDEX.md) | the kit's only plugin: always-on rules (`AGENTS.md`), hooks; path rules for code, tests, Godot, Java, Python, migrations, protocol, assets, Docker, spec and JSON; `reviewer` and `researcher` profiles; session, parallelize, review, git, security, investigate and Docker-host skills; the `sdd-*` pipeline, whose plan and implement steps carry the architecture, data, contract, coding, test and stack references (KIT-070); project and spec templates |
| [`platforms/`](platforms/) | machine tools ([`tools/`](platforms/tools/README.md)), validators and schemas ([`ci/`](platforms/ci/README.md)) with the spec-tools action a project's CI pins by commit SHA to run them ([`ci/actions/spec-tools/`](platforms/ci/actions/spec-tools/README.md), KIT-081: no copy in the project), files projects copy ([`kits/`](platforms/kits/README.md)), and the `just` modules and keyed-CSV merge driver a project runs from the installed kit (a justfile's `import '~/.ai-kit/platforms/kits/just/<profile>.just'`, KIT-081 stage 1b: no copy) |
| [`docs/`](docs/) | [`design.md`](docs/design.md) (principles and context costs), [`projects.md`](docs/projects.md) (what a consumer repository carries), [`features/`](docs/features/README.md) (KIT records) |
| `.devin-plugin/`, `.claude-plugin/`, `.agents/plugins/` | the content-free Devin meta-plugin, which requires `guardrails`, and the Claude Code and Codex marketplace catalogs |
| `.github/` | the required checks on every pull request and push to `main` (KIT-076: `ci.yml`: shellcheck, check, unit tests, install smoke, links, and `workflow-lint` (actionlint and zizmor over the workflows and templates, zizmor over the spec-tools action); `gitleaks.yml`: secrets scan; `codeql.yml`: CodeQL for Python and workflows, also weekly), the on-demand `evals.yml` (`claude plugin eval`), `release.yml` (tag `v*` → release), weekly Dependabot action updates (the workflows, the templates and the spec-tools action), the PR checklist template, the issue forms (`ISSUE_TEMPLATE/`: bug report, rule or skill proposal, and a link to private vulnerability reporting), `CODEOWNERS` and the community files [`CONTRIBUTING.md`](.github/CONTRIBUTING.md), [`SECURITY.md`](.github/SECURITY.md) and [`CODE_OF_CONDUCT.md`](.github/CODE_OF_CONDUCT.md) |

`plugins/guardrails/INDEX.md` is generated from the plugin's files by `platforms/tools/gen_index.py`. `VERSION` is the single source of the kit version: `check_kit.py`, `bump_version.py` and `release.yml` read it.

## Bootstrap

```bash
git clone https://github.com/ChristianPrzybulinski/agent-rules-kit.git ~/.ai-kit && ~/.ai-kit/platforms/tools/bootstrap.sh
```

## How each agent loads the kit

| Agent | Always-on | Skills/rules | Refresh |
|---|---|---|---|
| Devin Cloud | required plugin `plugins/guardrails/AGENTS.md` | `plugins/guardrails/skills/` and `plugins/guardrails/rules/` | fetches `main` per session |
| Devin CLI/Desktop | root meta-plugin requires `guardrails` | the required `guardrails` plugin | app startup; doctor updates stale SHA |
| Codex | `~/.codex/AGENTS.md` → `~/.ai-kit/plugins/guardrails/AGENTS.md` | marketplace plugins plus temporary fallback symlinks | launchd every six hours |
| Claude Code | `~/.claude/CLAUDE.md` → `~/.ai-kit/plugins/guardrails/AGENTS.md` | marketplace plugins; path rules from the plugin's path-rule hook in a repository `sync-project.sh` generated (KIT-081 stage 3: no `.claude/rules` copy, as no kit skill since stage 2b); user-level `~/.claude/rules/<plugin>-*.md` symlinks only with `AI_KIT_USER_RULES=1` | launchd every six hours |

User-level rule symlinks are opt-in with `AI_KIT_USER_RULES=1` (in a synced repository a rule then arrives both from `~/.claude/rules/` and from the plugin's hook); synced repos need nothing, and `doctor.sh` removes the old symlinks by default.

## Platform behavior

| Agent | Hooks | Path rules | Subagents | User-only skills |
|---|---|---|---|---|
| Devin Cloud | no | `globs` | managed Devins | `triggers: [user]` |
| Devin CLI/Desktop | PreToolUse guard and git context after a commit or PR, PostToolUse format/lint, SessionStart session-start checklist, synced-folder warning and git state after compaction, best effort | `globs` | shared profiles | `triggers: [user]` |
| Codex | no | the generated path-rule block in each folder's `AGENTS.md` (`sync-project.sh`, KIT-067), and the repo's own `.claude/rules/` on the `AGENTS.md` Boundaries line | no | `agents/openai.yaml` policy |
| Claude Code | PreToolUse guard and git context after a commit or PR, PostToolUse format/lint and path rules, SessionStart session-start checklist, synced-folder warning and git state after compaction, SubagentStart attribution line, InstructionsLoaded rule-load log (`skill_usage.py --rules`), best effort | `paths`, given by the plugin's PostToolUse hook in a synced repository (KIT-081 stage 3) | shared profiles | `disable-model-invocation: true` |

## Devin plugin

The existing repository source remains valid: the content-free root meta-plugin requires `guardrails`, so installing the repo installs the full kit:

```bash
devin plugins install ChristianPrzybulinski/agent-rules-kit               # guardrails
devin plugins install ChristianPrzybulinski/agent-rules-kit#plugins/guardrails  # the same plugin by path
```

Existing Customize entries need no source change; Reindex to pick up the new layout, and remove a `#plugins/dev` or `#plugins/sdd` entry, whose path no longer exists (KIT-047). The legacy `ai-kit` plugin should be removed (`devin plugins remove ai-kit`) — its path no longer exists. Run `devin plugins update` to force a local refresh.

## Codex

Bootstrap registers the marketplace and every plugin:

```bash
codex plugin marketplace add ChristianPrzybulinski/agent-rules-kit --ref stable   # the branch each release moves (KIT-081)
codex plugin add guardrails@ai-kit   # repeat per plugin, or let bootstrap/doctor iterate them
```

The marketplace follows the `stable` branch, which `release.yml` moves to each release tag (KIT-081), so `refresh.sh` reaches a new release with `codex plugin marketplace upgrade ai-kit`; a marketplace on another ref (`main`, or a tag from #271) is moved to `stable` once by `refresh.sh` or `doctor.sh` (a remove and an add, since Codex keeps a marketplace's source and ref together). The root marketplace catalog lists `guardrails`; `~/.codex/AGENTS.md` links to `~/.ai-kit/plugins/guardrails/AGENTS.md`. While [openai/codex#22078](https://github.com/openai/codex/issues/22078) remains open, doctor maintains fallback skill symlinks to `~/.ai-kit/plugins/*/skills/` and removes them once plugin skills are exposed. Codex keeps entries for retired plugin names (KIT-038, `dev` and `sdd` since KIT-047, `core` since KIT-055) in `~/.codex/config.toml`; `doctor.sh` removes each one the kit no longer ships with `codex plugin remove <name>@ai-kit`.

`bootstrap.sh`, `refresh.sh` and `doctor.sh` find the Codex CLI through `platforms/tools/codex-bin.sh`: `$CODEX_BIN` when set, then `codex` on `PATH`, then the CLI bundled in ChatGPT.app or Codex.app, then `~/.cache/codex-runtimes`. A `CODEX_BIN` that is not executable is reported and no other CLI is used. Run `platforms/tools/codex-bin.sh` to see which CLI the kit uses.

## Claude Code

```bash
claude plugin marketplace add "ChristianPrzybulinski/agent-rules-kit#stable"   # the branch each release moves (KIT-081)
claude plugin install guardrails@ai-kit
~/.ai-kit/platforms/tools/bootstrap.sh
```

The marketplace follows the `stable` branch, so `claude plugin marketplace update ai-kit` reaches each release. Claude Code keeps a marketplace's ref with its source and has no command that changes it, and `claude plugin marketplace remove` uninstalls the kit plugin and deletes its data folder (the rule-load log); so `refresh.sh` moves a marketplace on another ref (`main` before KIT-081) once: it copies `~/.claude/plugins/data/<plugin>-ai-kit/` to `${XDG_STATE_HOME:-~/.local/state}/ai-kit/plugin-data-backup/<UTC time>/`, removes the user-scope marketplace, adds it at `#stable`, installs the kit plugin again at user scope and copies the backup back (a file the reinstall wrote stays; the rule-load log keeps the backup's lines first), and keeps the backup. `doctor.sh` only reports a marketplace off `stable`, with that command.

Bootstrap links the shared AGENTS file to `~/.claude/CLAUDE.md` and narrows Devin imports so the same Claude file is not loaded twice. It links no path rule under `~/.claude/rules/` unless `AI_KIT_USER_RULES=1`: in a repository whose `CLAUDE.md` carries the `sync-project.sh` marker, the plugin's PostToolUse hook gives each rule the marker's profiles select, once per session, when a Read, Edit, Write, MultiEdit, NotebookEdit, Bash or Grep call names a file its globs match (KIT-081 stage 3; `sync-project.sh <repo>` removes the `.claude/rules` copies older syncs wrote). The marketplace `renames` map migrates installed retired names (`ai-kit`, the fourteen pre-KIT-038 plugins, `dev` and `sdd` since KIT-047, and `core` since KIT-055) to `guardrails`, and `forceRemoveDeletedPlugins` uninstalls the ones mapped to `null`; a renamed plugin loads after one `claude plugin install <name>@ai-kit`, which `refresh.sh` and `doctor.sh` run. `doctor.sh` warns about each `<name>@ai-kit` record the kit no longer ships, with the command for its scope, and `refresh.sh` runs `doctor.sh` when a pull leaves a kit link under `~/.claude` or `~/.codex` broken (KIT-055).

A synced repository enables only `guardrails@ai-kit` in `.claude/settings.json` (the guard hook lives in the plugin), which follows the `stable` branch, so every project on the machine uses the kit release the machine installed (KIT-081). The same file sets `includeGitInstructions` to `false`, so Claude Code's built-in commit and PR instructions and its git status snapshot do not compete with skill `git` (KIT-071). For sessions outside a synced repository, set the same key in `~/.claude/settings.json` or export `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS=1`; bootstrap and doctor never write it there, since that file stays the user's. To keep the built-in guidance in one repository, set `"includeGitInstructions": true` in its `.claude/settings.local.json`, which wins over the synced file. The setting also drops Claude Code's co-author trailer and PR footer, so the plugin states them at SessionStart and again at SubagentStart, since session-start context does not reach a subagent. It does so only while the user, project and local settings files leave `includeGitInstructions` at `false` (or `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS=1`), and your own attribution wins: a custom `attribution.commit` or `attribution.pr` replaces the default trailer or footer, an empty one drops it, and `attribution: false` or `includeCoAuthoredBy: false` drops both. `--settings` and managed settings are not read. The vendored mode that pinned a kit version per project (`sync-project.sh --vendor-skills`, KIT-072) was removed in KIT-081 stage 2b: the flag exits 2, and a plain `sync-project.sh <repo>` migrates a vendored repository by removing the kit-marked copies (`.claude/skills/<name>/`, `.claude/skills/guardrails-pinned/`, `.claude/ai-kit/`, `KIT_MANIFEST.json`) and the pin's hooks and key from `.claude/settings.json`, keeping the project's own files; [`docs/projects.md`](docs/projects.md#no-kit-copies-in-the-project-kit-081-stage-2b) has the steps.

## Refresh and diagnosis

On macOS, launchd runs `platforms/tools/refresh.sh` at login and every six hours. The user install follows the release, not `main` (#271): `refresh.sh` fetches the tags and checks the clone out detached at the newest `vX.Y.Z` tag on `origin/main`, so the always-on `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md` links and the kit tools change only with a release, and a kit merge waits for its tag. The Claude Code and Codex marketplaces and Devin's team plugin follow the `stable` branch, which `release.yml` moves to the released commit after publishing the release, fast-forward only (KIT-081), so a release reaches them through a plain update and no ref changes per release. `platforms/tools/doctor.sh` fails when the clone is not at the newest release or the Claude Code, Codex or Devin ref is not `stable` (it moves Codex itself, and for Claude Code names `refresh.sh`, whose move backs up the plugin data), and repairs clone, plugin and symlink state, warns when a Claude plugin cache differs from the kit (`refresh.sh` reinstalls it, KIT-013), and sets Claude Code's `autoCompactWindow` to the number `300000` when `~/.claude/settings.json` has none or holds the `"200k"` an older doctor wrote (KIT-010). When its last run is 7 or more days old, `refresh.sh` also runs `platforms/tools/session_audit.py`, the weekly cross-session audit pre-filter that skill `session` reads in `audit` mode; it prints counts only, and `AI_KIT_SESSION_AUDIT=0` turns it off (KIT-056). Nothing refreshes at agent session start.

## Maintainers

Changes follow [`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md): where each kind of content goes, the release steps, and the checks to run before a PR (`platforms/tools/check.sh` and `platforms/tools/smoke.sh`).

## License

[MIT](LICENSE). The kit vendors no third-party skill: KIT-070 removed `grilling`, the last one, and KIT-083 the vendoring tool and its lock.
