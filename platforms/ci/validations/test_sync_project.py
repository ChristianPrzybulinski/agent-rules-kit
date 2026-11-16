"""sync-project.sh --check: stale kit path scan on a throwaway repo."""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from collections import OrderedDict
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("platforms/tools/sync-project.sh", "platforms/tools/sync_agents_md.py", "platforms/tools/sync_just.py",
          "platforms/tools/sync_unvendor.py", "platforms/tools/sync-profiles.txt", "plugins/guardrails/**",
          "platforms/kits/just/**", "platforms/kits/github/workflows/spec-lint.yml",
          "platforms/kits/godot/scripts/**", "platforms/ci/validations/check_spec.py",
          "platforms/ci/validations/row_checks.py", "platforms/ci/validations/pr_gates.py",
          "platforms/ci/validations/spec_trace.py", "platforms/ci/validations/check_docs_structure.py",
          "platforms/ci/schemas/**")

SCRIPT = Path(__file__).resolve().parent.parent.parent / "tools" / "sync-project.sh"
KIT = SCRIPT.parents[2]
VERSION = (KIT / "VERSION").read_text(encoding="utf-8").strip()
MAP = KIT / "platforms" / "tools" / "sync-profiles.txt"  # KIT-047: one plugin, the map picks the copies
PLUGIN = KIT / "plugins" / "guardrails"
PINNED = "guardrails-pinned"  # KIT-072's pinned copy of the plugin, which KIT-081 stage 2b removes from a project
HEAD_TOOL = "~/.ai-kit/platforms/"  # B2: a kit tool or template the skills and rules call from the kit clone
PINNED_TOOL = '"$(git rev-parse --show-toplevel)"/.claude/ai-kit/platforms/'  # ... and from KIT-072's pin, gone since 2b

STALE = "- agent-rules-kit `kits/java-maven/pom-parent.xml` requires [25,26)"


class SyncProjectCheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        (self.repo / "AGENTS.md").write_text("# x\n")
        (self.repo / "docs" / "spec").mkdir(parents=True, exist_ok=True)
        install = self.run_sync()  # install once: --check diffs the copied files
        self.assertEqual(install.returncode, 0, install.stdout + install.stderr)

    def tearDown(self):
        self.tmp.cleanup()

    def run_sync(self, *args, repo=None, home=None, env=None):
        full = dict(os.environ)
        if home:
            full["HOME"] = str(home)
        full.update(env or {})
        return subprocess.run(["bash", str(SCRIPT), *args, str(repo or self.repo)],
                              capture_output=True, text=True, errors="replace", check=False, env=full)

    def write_md(self, rel, text):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def test_clean_repo_passes(self):
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("consistent with kit", result.stdout)

    def test_stale_citation_fails(self):
        self.write_md("docs/spec/decisions/DEC-001-x.md", "# DEC-001\n\n" + STALE + "\n")
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("stale kit path: docs/spec/decisions/DEC-001-x.md:3", result.stdout)

    def test_opt_out_marker_passes(self):
        self.write_md("docs/spec/decisions/DEC-001-x.md",
                      "# DEC-001\n\n" + STALE + " <!-- kit-path-ok -->\n")
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_no_false_positives(self):
        self.write_md("docs/ci.md", "CI runs platforms/kits/github/workflows/spec-lint.yml\n")
        self.write_md("docs/sessions/2026-01-01-x.md", "back then it was agents/skills/\n")
        self.write_md(".claude/skills/x/references/y.md", "a project knowledge/ folder\n")
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_a_changelog_is_history_for_both_scans(self):  # #299
        line = STALE + "; the `testing` skill\n"
        for rel in ("CHANGELOG.md", "server/CHANGELOG.md"):
            self.write_md(rel, "# Changelog\n\n" + line)
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.write_md("docs/x.md", line)
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("stale kit path: docs/x.md:1:", result.stdout)
        self.assertIn("removed kit skill: docs/x.md:1:", result.stdout)
        self.assertNotIn("CHANGELOG.md", result.stdout)

    def test_exclusion_matches_path_only(self):
        self.write_md("docs/x.md", "moved out of docs/legacy/ into agents/skills/\n")
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("stale kit path: docs/x.md", result.stdout)

    def test_11x_plugin_layouts_fail(self):  # KIT-061: the 11.x plugin folders before guardrails
        self.write_md("docs/x.md", "- Process: agent-rules-kit `plugins/sdd/skills/sdd-constitution/references/sdd-process.md`\n"
                      "- Java: `plugins/dev/skills/java-standards/SKILL.md`\n"
                      "- Templates: `plugins/architect-sdd/templates/spec-journey.md`\n")
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 1)
        for line in (1, 2, 3):
            self.assertIn(f"stale kit path: docs/x.md:{line}:", result.stdout)

    def test_older_plugin_folders_fail(self):  # KIT-062: every plugins/ folder of the kit's history before guardrails
        folders = ["all/x.md", "dev-core/x.md", "dev-godot/x.md", "dev-java/x.md", "extras/x.md", "infra-core/x.md",
                   "infra-github/x.md", "infra-persistence/x.md", "process-loop/x.md", "quality-core/x.md",
                   "quality-security/x.md"]
        self.write_md("docs/x.md", "".join(f"- agent-rules-kit `plugins/{f}`\n" for f in folders))
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 1)
        for line in range(1, len(folders) + 1):
            self.assertIn(f"stale kit path: docs/x.md:{line}:", result.stdout)

    def test_current_plugin_layout_passes(self):  # KIT-061
        self.write_md("docs/x.md", "- Process: agent-rules-kit `plugins/guardrails/skills/sdd-constitution/references/sdd-process.md`\n")
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_synced_folder_warning(self):  # KIT-021
        home = self.repo / "home"
        repo = home / "Library" / "CloudStorage" / "Dropbox" / "repo"
        (repo / "docs" / "spec").mkdir(parents=True)
        (repo / "AGENTS.md").write_text("# x\n")
        # The hook warns only for a repository (KIT-058), so both targets get a .git entry.
        (repo / ".git").mkdir()
        (self.repo / ".git").mkdir()
        for args in ((), ("--check",)):
            result = self.run_sync(*args, repo=repo, home=home)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("sync: warning: ai-kit: ", result.stderr)
            self.assertIn("is inside the cloud-synced folder", result.stderr)
        self.assertNotIn("cloud-synced", self.run_sync("--check", home=home).stderr)

    def test_install_generates_profile_files_and_is_idempotent(self):
        claude = self.repo / "CLAUDE.md"
        settings = self.repo / ".claude" / "settings.json"
        self.assertEqual(claude.read_text().splitlines(), [
            f"<!-- generated by agent-rules-kit sync-project.sh v{VERSION}; profile docs;"  # KIT-081 stage 2b
            " AGENTS.md is the source -->",
            "@AGENTS.md"])
        data = json.loads(settings.read_text())
        self.assertEqual(data["extraKnownMarketplaces"]["ai-kit"],
                         {"source": {"source": "github",
                                     "repo": "ChristianPrzybulinski/agent-rules-kit",
                                     "ref": "stable"}})  # KIT-081: the user's marketplace is ...#stable too
        ai_kit = {k for k in data["enabledPlugins"] if k.endswith("@ai-kit")}
        self.assertEqual(ai_kit, {"guardrails@ai-kit"})
        self.assertTrue(all(data["enabledPlugins"][k] is True for k in ai_kit))
        self.assertIs(data["includeGitInstructions"], False)  # KIT-071
        before = (claude.read_bytes(), settings.read_bytes())
        second = self.run_sync()
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertEqual(before, (claude.read_bytes(), settings.read_bytes()))

    def test_marketplace_source_without_the_stable_ref_diverges_and_a_sync_adds_it(self):  # KIT-081
        # A project source without the ref conflicts with the user's ...#stable marketplace in Claude Code.
        settings = self.repo / ".claude" / "settings.json"
        data = json.loads(settings.read_text())
        data["extraKnownMarketplaces"]["ai-kit"] = {"source": {"source": "github",
                                                              "repo": "ChristianPrzybulinski/agent-rules-kit"}}
        settings.write_text(json.dumps(data, indent=2) + "\n")
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("sync: .claude/settings.json diverges for profile docs (marketplace: ai-kit)", result.stdout)
        resync = self.run_sync()
        self.assertEqual(resync.returncode, 0, resync.stdout + resync.stderr)
        self.assertEqual(json.loads(settings.read_text())["extraKnownMarketplaces"]["ai-kit"]["source"]["ref"],
                         "stable")
        check = self.run_sync("--check")
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    def test_check_detects_enabled_plugins_drift(self):
        settings = self.repo / ".claude" / "settings.json"
        data = json.loads(settings.read_text())
        data["enabledPlugins"]["dev@ai-kit"] = True
        settings.write_text(json.dumps(data, indent=2) + "\n")
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("diverges for profile docs", result.stdout)

    def test_check_detects_git_instructions_drift(self):  # KIT-071
        settings = self.repo / ".claude" / "settings.json"
        for value in (True, None):
            data = json.loads(settings.read_text())
            if value is None:
                data.pop("includeGitInstructions")
            else:
                data["includeGitInstructions"] = value
            settings.write_text(json.dumps(data, indent=2) + "\n")
            result = self.run_sync("--check")
            self.assertEqual(result.returncode, 1, value)
            self.assertIn("includeGitInstructions: want false", result.stdout)
        self.assertEqual(self.run_sync().returncode, 0)
        self.assertIs(json.loads(settings.read_text())["includeGitInstructions"], False)
        self.assertEqual(self.run_sync("--check").returncode, 0)

    def test_check_fails_without_claude_md(self):
        (self.repo / "CLAUDE.md").unlink()
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("CLAUDE.md missing", result.stdout)

    def test_handwritten_claude_md_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as other:
            repo = Path(other)
            (repo / "AGENTS.md").write_text("# x\n")
            (repo / "pom.xml").write_text("<project/>\n")
            (repo / "CLAUDE.md").write_text("# mine\n")
            result = self.run_sync(repo=repo)
            self.assertEqual(result.returncode, 1)
            self.assertIn("is not generated", result.stdout + result.stderr)
            self.assertEqual((repo / "CLAUDE.md").read_text(), "# mine\n")
            self.assertFalse((repo / ".claude" / "settings.json").exists())
            self.assertFalse((repo / ".github").exists())

    def test_multi_profile_union_and_folder_scope(self):  # KIT-016
        result = self.run_sync("--profile", "java:server,docs,godot:client/")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        rules = self.repo / ".claude" / "rules"
        self.assertEqual(sorted(p.name for p in rules.glob("*.md")),
                         ["guardrails-assets.md", "guardrails-code.md", "guardrails-docker.md", "guardrails-godot.md",
                          "guardrails-java.md", "guardrails-json.md", "guardrails-migrations.md", "guardrails-protocol.md",
                          "guardrails-python.md", "guardrails-spec.md", "guardrails-tests.md"])
        self.assertIn('  - "client/**/*.gd"', (rules / "guardrails-godot.md").read_text().splitlines())
        # docker goes to the code profiles only, so it takes their folders and never the docs root (KIT-071)
        docker_globs = (rules / "guardrails-docker.md").read_text().splitlines()
        self.assertIn('  - "server/**/compose*.yml"', docker_globs)
        self.assertIn('  - "client/**/Dockerfile*"', docker_globs)
        self.assertNotIn('  - "**/compose*.yml"', docker_globs)
        # json is named after no profile and docs covers the root, so it keeps the whole repository (KIT-059)
        self.assertIn('  - "**/*.json"', (rules / "guardrails-json.md").read_text().splitlines())
        self.assertIn('  - "server/**/*.java"', (rules / "guardrails-java.md").read_text().splitlines())
        self.assertIn('  - "docs/spec/**/*.md"', (rules / "guardrails-spec.md").read_text().splitlines())
        # the map sends both rules to every godot, java or python profile; each takes only the folder
        # of the profile it is named after
        self.assertNotIn("server/", (rules / "guardrails-godot.md").read_text())
        self.assertNotIn("client/", (rules / "guardrails-java.md").read_text())
        settings = json.loads((self.repo / ".claude" / "settings.json").read_text())
        self.assertEqual({k for k in settings["enabledPlugins"] if k.endswith("@ai-kit")},
                         {"guardrails@ai-kit"})
        check = self.run_sync("--check", "--profile", "docs,godot:client,java:server")
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        single = self.run_sync("--check", "--profile", "docs")
        self.assertEqual(single.returncode, 1)
        self.assertIn("guardrails-java.md is generated but not in profile", single.stdout)
        alone = self.run_sync("--profile", "godot:client")
        self.assertEqual(alone.returncode, 0, alone.stdout + alone.stderr)
        # no java profile: the java rule takes the folders of every profile the map sends it to
        self.assertIn('  - "client/**/*.java"', (rules / "guardrails-java.md").read_text().splitlines())

    def test_python_profile_scopes_the_python_rule(self):  # KIT-045
        result = self.run_sync("--profile", "docs,godot:client,java:server,python:platform,python:tools")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        rules = self.repo / ".claude" / "rules"
        python_rule = (rules / "guardrails-python.md").read_text().splitlines()
        for glob in ("platform/**/*.py", "tools/**/*.py", "platform/**/pyproject.toml"):
            self.assertIn(f'  - "{glob}"', python_rule)
        self.assertNotIn("client/", "\n".join(python_rule))
        self.assertNotIn("platform/", (rules / "guardrails-godot.md").read_text())
        self.assertNotIn("platform/", (rules / "guardrails-java.md").read_text())
        check = self.run_sync("--check", "--profile", "python:tools,docs,python:platform,godot:client,java:server")
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    def test_rule_from_the_old_plugin_name_is_replaced(self):  # KIT-047
        result = self.run_sync("--profile", "docs,godot")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        rules = self.repo / ".claude" / "rules"
        old = rules / "dev-godot.md"
        old.write_text((rules / "guardrails-godot.md").read_text())
        check = self.run_sync("--check", "--profile", "docs,godot")
        self.assertEqual(check.returncode, 1)
        self.assertIn("dev-godot.md is generated but not in profile", check.stdout)
        write = self.run_sync("--profile", "docs,godot")
        self.assertEqual(write.returncode, 0, write.stdout + write.stderr)
        self.assertFalse(old.exists())
        self.assertTrue((rules / "guardrails-godot.md").is_file())

    def test_rule_from_the_core_plugin_name_is_replaced(self):  # KIT-055
        result = self.run_sync("--profile", "docs,godot")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        rules = self.repo / ".claude" / "rules"
        old = rules / "core-godot.md"
        old.write_text((rules / "guardrails-godot.md").read_text())
        check = self.run_sync("--check", "--profile", "docs,godot")
        self.assertEqual(check.returncode, 1)
        self.assertIn("core-godot.md is generated but not in profile", check.stdout)
        write = self.run_sync("--profile", "docs,godot")
        self.assertEqual(write.returncode, 0, write.stdout + write.stderr)
        self.assertFalse(old.exists())
        self.assertTrue((rules / "guardrails-godot.md").is_file())

    def test_check_reports_the_core_plugin_in_settings(self):  # KIT-055
        result = self.run_sync("--profile", "docs")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        settings_path = self.repo / ".claude" / "settings.json"
        settings = json.loads(settings_path.read_text())
        settings["enabledPlugins"]["core@ai-kit"] = True
        settings_path.write_text(json.dumps(settings, indent=2) + "\n")
        check = self.run_sync("--check", "--profile", "docs")
        self.assertEqual(check.returncode, 1)
        self.assertIn("extra: core@ai-kit", check.stdout)
        write = self.run_sync("--profile", "docs")
        self.assertEqual(write.returncode, 0, write.stdout + write.stderr)
        self.assertEqual({k for k in json.loads(settings_path.read_text())["enabledPlugins"] if k.endswith("@ai-kit")},
                         {"guardrails@ai-kit"})

    def test_multi_profile_rejects_unknown_profile_and_outside_folder(self):
        for value in ("docs,rust", "godot:../client", "godot:/client", "docs,"):
            result = self.run_sync("--profile", value)
            self.assertEqual(result.returncode, 2, value)

    def claude_state(self):
        return {f: f.read_bytes() for f in (self.repo / ".claude").rglob("*") if f.is_file()}

    def claude_md(self, profile, version=VERSION):
        """The generated CLAUDE.md: its marker records the profile list since KIT-081 stage 2b, before it no list."""
        recorded = f" profile {profile};" if profile is not None else ""
        return (f"<!-- generated by agent-rules-kit sync-project.sh v{version};{recorded} AGENTS.md is the source -->\n"
                "@AGENTS.md\n")

    def test_claude_md_profile_list_is_sticky(self):  # KIT-017, KIT-081 stage 2b: the marker, not KIT_MANIFEST.json
        write = self.run_sync("--profile", "docs,godot:client,java:server")
        self.assertEqual(write.returncode, 0, write.stdout + write.stderr)
        self.assertEqual(self.text("CLAUDE.md"), self.claude_md("docs,godot:client,java:server"))
        before = self.claude_state() | {"CLAUDE.md": self.text("CLAUDE.md")}
        check = self.run_sync("--check")
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        self.assertIn("sync: profile=docs,godot:client,java:server (CLAUDE.md)", check.stdout)
        write = self.run_sync()
        self.assertEqual(write.returncode, 0, write.stdout + write.stderr)
        self.assertIn("sync: profile=docs,godot:client,java:server (CLAUDE.md)", write.stdout)
        self.assertIn("[0 written, 0 removed]", write.stdout)
        self.assertNotIn("sync: removed", write.stdout)
        self.assertEqual(before, self.claude_state() | {"CLAUDE.md": self.text("CLAUDE.md")})

    def test_explicit_profile_overrides_the_recorded_list(self):  # KIT-017, KIT-081 stage 2b
        write = self.run_sync("--profile", "docs,godot:client,java:server")
        self.assertEqual(write.returncode, 0, write.stdout + write.stderr)
        check = self.run_sync("--check", "--profile", "docs")
        self.assertEqual(check.returncode, 1)
        self.assertIn("sync: profile=docs (--profile)", check.stdout)
        self.assertIn("sync: CLAUDE.md records profile 'docs,godot:client,java:server' expected 'docs'", check.stdout)
        write = self.run_sync("--profile", "docs")
        self.assertEqual(write.returncode, 0, write.stdout + write.stderr)
        self.assertFalse((self.repo / ".claude" / "rules" / "guardrails-godot.md").exists())
        self.assertEqual(self.text("CLAUDE.md"), self.claude_md("docs"))
        bare = self.run_sync("--check")
        self.assertEqual(bare.returncode, 0, bare.stdout + bare.stderr)
        self.assertIn("sync: profile=docs (CLAUDE.md)", bare.stdout)

    def test_claude_md_without_a_valid_profile(self):  # KIT-017, KIT-081 stage 2b
        claude = self.repo / "CLAUDE.md"
        claude.write_text(self.claude_md(None))  # a CLAUDE.md from before the marker recorded the list
        result = self.run_sync("--check")  # no recorded list: inference decides
        self.assertIn("sync: profile=docs (inferred)", result.stdout)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("sync: CLAUDE.md missing or diverges (rerun sync-project.sh)", result.stdout)
        claude.write_text(self.claude_md("docs,rust"))
        before = self.claude_state() | {"CLAUDE.md": self.text("CLAUDE.md")}
        result = self.run_sync()
        self.assertEqual(result.returncode, 2)
        self.assertIn("sync: CLAUDE.md records that profile; pass --profile to replace it", result.stderr)
        self.assertEqual(before, self.claude_state() | {"CLAUDE.md": self.text("CLAUDE.md")})

    # KIT-067: spec.md sdd.rule_paths scopes a rule's globs; a block in each folder's AGENTS.md carries the rules for
    # agents that load no rule by path.

    def spec_md(self, extra):
        (self.repo / "docs" / "spec" / "spec.md").write_text(SPEC_MD.format(extra=extra))

    def text(self, rel):
        return (self.repo / rel).read_text()

    def test_rule_paths_scope_a_rule_and_check_flags_drift(self):
        self.spec_md("sdd:\n  rule_paths:\n    json: [game/protocol]\n    godot: [game/client]\n")
        result = self.run_sync("--profile", "docs,godot:client")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        rules = self.repo / ".claude" / "rules"
        json_rule = (rules / "guardrails-json.md").read_text().splitlines()
        self.assertIn('  - "game/protocol/**/*.json"', json_rule)
        self.assertNotIn('  - "**/*.json"', json_rule)
        # the parameter wins over the profile folder
        self.assertIn('  - "game/client/**/*.gd"', (rules / "guardrails-godot.md").read_text().splitlines())
        self.assertNotIn('"client/', (rules / "guardrails-godot.md").read_text())
        self.assertIn('  - "docs/spec/**/*.md"', (rules / "guardrails-spec.md").read_text().splitlines())
        check = self.run_sync("--check", "--profile", "docs,godot:client")
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        self.spec_md("sdd:\n  rule_paths:\n    json: [game/content]\n    godot: [game/client]\n")
        drift = self.run_sync("--check", "--profile", "docs,godot:client")
        self.assertEqual(drift.returncode, 1)
        self.assertIn("sync: .claude/rules/guardrails-json.md diverges from the kit", drift.stdout)

    def test_rule_paths_name_a_kit_rule(self):
        self.spec_md("sdd:\n  rule_paths: {nope: [x]}\n")
        before = self.claude_state()
        for args in ((), ("--check",)):
            result = self.run_sync(*args)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("sdd.rule_paths names rule 'nope', which the kit does not ship", result.stderr)
        self.assertEqual(before, self.claude_state())

    def test_invalid_sdd_block_refuses_the_sync(self):
        self.spec_md("sdd:\n  tracker: jira\n")
        before = self.claude_state()
        for args in ((), ("--check",)):
            result = self.run_sync(*args)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("sdd.tracker 'jira' is not one of ['github', 'none']", result.stderr)
        self.assertEqual(before, self.claude_state())

    def test_agents_md_block_per_folder(self):
        for folder in ("client", "server"):
            (self.repo / folder).mkdir()
        (self.repo / "client" / "AGENTS.md").write_text("# Client\n\nHand-written line.\n")
        profile = ("--profile", "docs,godot:client,java:server")
        result = self.run_sync(*profile)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        godot, java, json_, python, spec = (rule_bullet(name) for name in ("godot", "java", "json", "python", "spec"))
        client = self.text("client/AGENTS.md")
        self.assertTrue(client.startswith("# Client\n\nHand-written line.\n\n" + BLOCK_BEGIN), client)
        self.assertTrue(client.endswith(BLOCK_END + "\n"), client)
        self.assertIn(godot, client)
        self.assertIn("`client/**/*.gd`", client)
        self.assertNotIn(java, client)
        server = self.text("server/AGENTS.md")
        self.assertTrue(server.startswith(BLOCK_BEGIN), server)
        self.assertIn(java, server)
        self.assertIn("`server/**/*.java`", server)
        self.assertNotIn(godot, server)
        spec_agents = self.text("docs/spec/AGENTS.md")
        self.assertIn(spec, spec_agents)
        self.assertIn("`docs/spec/**/*.md`", spec_agents)
        root = self.text("AGENTS.md")
        self.assertTrue(root.startswith("# x\n"), root)
        self.assertIn(json_, root)
        for absent in (godot, java, spec):
            self.assertNotIn(absent, root)
        # the map sends the python rule to godot and java profiles, but no profile is python: no AGENTS.md block
        for rel in ("AGENTS.md", "client/AGENTS.md", "server/AGENTS.md", "docs/spec/AGENTS.md"):
            self.assertNotIn(python, self.text(rel))
        before = {rel: self.text(rel) for rel in ("AGENTS.md", "client/AGENTS.md", "server/AGENTS.md")}
        check = self.run_sync("--check", *profile)
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        again = self.run_sync(*profile)
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertEqual(before, {rel: self.text(rel) for rel in before})

    def test_check_flags_agents_md_drift(self):
        for folder in ("client", "server"):
            (self.repo / folder).mkdir()
        profile = ("--profile", "docs,godot:client,java:server")
        self.assertEqual(self.run_sync(*profile).returncode, 0)
        client = self.repo / "client" / "AGENTS.md"
        client.write_text(client.read_text().replace(rule_bullet("godot"), "- edited by hand"))
        (self.repo / "server" / "AGENTS.md").unlink()
        check = self.run_sync("--check", *profile)
        self.assertEqual(check.returncode, 1)
        self.assertIn("sync: client/AGENTS.md path-rule block diverges from the kit", check.stdout)
        self.assertIn("sync: server/AGENTS.md path-rule block missing", check.stdout)
        self.assertEqual(self.run_sync(*profile).returncode, 0)
        self.assertEqual(self.run_sync("--check", *profile).returncode, 0)
        narrow = self.run_sync("--check", "--profile", "docs,godot:client")
        self.assertEqual(narrow.returncode, 1)
        self.assertIn("sync: server/AGENTS.md path-rule block is generated but not in profile", narrow.stdout)
        write = self.run_sync("--profile", "docs,godot:client")
        self.assertEqual(write.returncode, 0, write.stdout + write.stderr)
        self.assertFalse((self.repo / "server" / "AGENTS.md").exists(), "a file that held only the block goes")
        self.assertIn(rule_bullet("godot"), client.read_text())

    def test_agents_md_block_follows_rule_paths(self):
        self.assertIn(BLOCK_BEGIN, self.text("AGENTS.md"), "setUp's docs install puts the json block at the root")
        (self.repo / "game" / "protocol").mkdir(parents=True)
        # the docs profile also sends the protocol rule to the root (KIT-070); move it too so no rule stays there
        self.spec_md("sdd:\n  rule_paths: {json: [game/protocol], protocol: [game]}\n")
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.text("AGENTS.md"), "# x\n", "the block leaves a hand-written file as it was")
        self.assertIn("`game/**/protocol/**`", self.text("game/AGENTS.md"))
        self.assertIn(rule_bullet("json"), self.text("game/protocol/AGENTS.md"))
        self.assertIn("`game/protocol/**/*.json`", self.text("game/protocol/AGENTS.md"))

    # KIT-067 review fix round: the block never leaves the repository, and the refusal runs before the sync's first
    # write; a rule_paths entry that does nothing says so. The block logic itself (line endings, removal, broken
    # markers, symbolic links, nested checkouts, missing and skipped folders) is tested in-process in
    # test_sync_agents_md.py (KIT-077).

    def outside_dir(self):
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside)
        return outside

    def test_agents_md_refuses_a_folder_outside_the_repo(self):
        outside = self.outside_dir()
        (self.repo / "game").mkdir()
        os.symlink(outside, self.repo / "game" / "protocol")
        self.spec_md("sdd:\n  rule_paths: {json: [game/protocol]}\n")
        before = self.claude_state()
        message = "sync: game/protocol goes through a symbolic link; the sync writes no path-rule block there"
        for args in ((), ("--check",)):
            result = self.run_sync(*args)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn(message, result.stdout)
        self.assertFalse((outside / "AGENTS.md").exists())
        self.assertEqual(before, self.claude_state(), "the refusal runs before the first write")

    def test_rule_paths_for_a_rule_outside_the_profile_warns(self):
        self.spec_md("sdd:\n  rule_paths: {godot: [client]}\n")
        result = self.run_sync("--profile", "docs")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("sync: warning: sdd.rule_paths.godot does nothing: profile docs receives no rules/godot.md",
                      result.stderr)

    # KIT-081 stage 2b: the vendored mode (KIT-072) is gone; a project uses guardrails@ai-kit. A repository synced in
    # that mode holds KIT_MANIFEST.json, the skill copies and .claude/skills/guardrails-pinned/ marked .agent-rules-kit,
    # .claude/ai-kit/ (the kit hooks as scripts and the tools), and in .claude/settings.json the hooks that run those
    # scripts, guardrails-pinned@skills-dir on and guardrails@ai-kit off. A sync removes the kit-marked state only.

    def scratch(self):
        """A folder outside the test repository, which the stale-path scan must not read."""
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        return Path(scratch.name)

    def pinned(self, rel=""):
        return self.repo / ".claude" / "skills" / PINNED / rel

    def settings(self, name="settings.json"):
        return json.loads((self.repo / ".claude" / name).read_text())

    def write_settings(self, data, name="settings.json"):
        (self.repo / ".claude" / name).write_text(json.dumps(data, indent=2) + "\n")

    def vendored_texts(self):
        """Every generated text a session reads in the repo: skill copies, rules and the AGENTS.md blocks."""
        roots = [self.repo / ".claude" / "skills", self.repo / ".claude" / "rules"]
        files = [f for root in roots for f in root.rglob("*.md")] + list(self.repo.rglob("AGENTS.md"))
        return {f: f.read_text() for f in files}

    VENDORED_SKILLS = ("investigate", "sdd-tasks")
    OWN_HOOK = OrderedDict(matcher="Bash", hooks=[OrderedDict(type="command", command="echo own")])

    def kit_hook(self, event, group):
        """A settings hook group as KIT-072's pin wrote it: a handler that runs a script under .claude/ai-kit/hooks/."""
        return OrderedDict(matcher="Bash", hooks=[OrderedDict(
            type="command", command=f'bash "${{CLAUDE_PROJECT_DIR}}/.claude/ai-kit/hooks/{event}-{group}-0.sh"',
            timeout=10)])

    def mark(self, folder, source):
        (folder / ".agent-rules-kit").write_text(
            f"{source} kit 13.1.0 generated by platforms/tools/sync-project.sh; do not edit\n")

    def vendor(self, profile="docs,godot:client", parts=("manifest", "skills", "pinned", "kit_dir", "key", "hooks"),
               release=True):
        """Writes the state a 13.1.0 `sync-project.sh --vendor-skills --profile <profile>` left, part by part; with
        release, also guardrails@ai-kit off and the CLAUDE.md of that release, whose marker records no profile list."""
        claude = self.repo / ".claude"
        skills = claude / "skills"
        skills.mkdir(parents=True, exist_ok=True)
        if "skills" in parts:
            for name in self.VENDORED_SKILLS:
                shutil.copytree(PLUGIN / "skills" / name, skills / name)
                self.mark(skills / name, f"plugins/guardrails/skills/{name}")
        if "pinned" in parts:
            (skills / PINNED / ".claude-plugin").mkdir(parents=True)
            (skills / PINNED / ".claude-plugin" / "plugin.json").write_text('{"name": "guardrails-pinned"}\n')
            (skills / PINNED / "agents").mkdir()
            (skills / PINNED / "agents" / "reviewer.md").write_text("---\nname: reviewer\n---\n")
            self.mark(skills / PINNED, "plugins/guardrails")
        if "kit_dir" in parts:
            (claude / "ai-kit" / "hooks").mkdir(parents=True)
            (claude / "ai-kit" / "hooks" / "PreToolUse-0-0.sh").write_text("#!/bin/bash\nexit 0\n")
            (claude / "ai-kit" / "platforms" / "tools").mkdir(parents=True)
            (claude / "ai-kit" / "platforms" / "tools" / "review_checks.py").write_text("print('pinned')\n")
            self.mark(claude / "ai-kit", "plugins/guardrails")
        if "manifest" in parts:
            (skills / "KIT_MANIFEST.json").write_text(json.dumps({
                "KIT_VERSION": "13.1.0", "generator": "platforms/tools/sync-project.sh", "profile": profile,
                "KIT_COMMIT": "5a4924e" + "0" * 33, "skills": {name: {"plugin": "guardrails", "files": {}}
                                                             for name in self.VENDORED_SKILLS}}, indent=2) + "\n")
        data = json.loads((claude / "settings.json").read_text(), object_pairs_hook=OrderedDict)
        data["permissions"] = OrderedDict(allow=["Bash(ls)"])
        data["enabledPlugins"] = OrderedDict([("guardrails@ai-kit", not release), ("other@market", True)])
        if "key" in parts:
            data["enabledPlugins"][f"{PINNED}@skills-dir"] = True
        data["hooks"] = OrderedDict(PreToolUse=[self.OWN_HOOK], Stop=[self.OWN_HOOK])
        if "hooks" in parts:
            data["hooks"]["PreToolUse"].append(self.kit_hook("PreToolUse", 0))
            data["hooks"]["SessionStart"] = [self.kit_hook("SessionStart", 0)]
        self.write_settings(data)
        if release:
            (self.repo / "CLAUDE.md").write_text(self.claude_md(None, "13.1.0"))

    def test_a_vendored_repo_becomes_a_plugins_repo(self):
        (self.repo / "client").mkdir()
        self.vendor()
        check = self.run_sync("--check")
        self.assertEqual(check.returncode, 1, check.stdout + check.stderr)
        self.assertIn("sync: profile=docs,godot:client (manifest)", check.stdout)  # the migration keeps the list
        for rel in (".claude/skills/investigate", ".claude/skills/sdd-tasks", f".claude/skills/{PINNED}",
                    ".claude/skills/KIT_MANIFEST.json", ".claude/ai-kit",
                    f".claude/settings.json enabledPlugins {PINNED}@skills-dir",
                    ".claude/settings.json hooks that run .claude/ai-kit/hooks/"):
            self.assertIn(f"sync: vendored kit state left: {rel}: ", check.stdout)
        self.assertIn(f"run platforms/tools/sync-project.sh {self.repo} once", check.stdout)
        own = self.repo / ".claude" / "skills" / "review-loop"  # the project's own skill, never touched
        own.mkdir()
        (own / "SKILL.md").write_text("mine\n")
        write = self.run_sync()
        self.assertEqual(write.returncode, 0, write.stdout + write.stderr)
        self.assertIn("sync: profile=docs,godot:client (manifest)", write.stdout)
        for rel in (".claude/skills/investigate", ".claude/skills/sdd-tasks", f".claude/skills/{PINNED}",
                    ".claude/skills/KIT_MANIFEST.json", ".claude/ai-kit"):
            self.assertIn(f"sync: removed {rel}: ", write.stdout)
            self.assertFalse((self.repo / rel).exists(), rel)
        self.assertEqual((own / "SKILL.md").read_text(), "mine\n")
        self.assertEqual(self.text("CLAUDE.md"), self.claude_md("docs,godot:client"))
        data = self.settings()
        self.assertEqual(data["enabledPlugins"], {"other@market": True, "guardrails@ai-kit": True})
        self.assertEqual(data["hooks"], {"PreToolUse": [self.OWN_HOOK], "Stop": [self.OWN_HOOK]})
        self.assertEqual(data["permissions"], {"allow": ["Bash(ls)"]})
        self.assertTrue((self.repo / ".claude" / "rules" / "guardrails-godot.md").is_file())
        check = self.run_sync("--check")
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        self.assertIn("sync: profile=docs,godot:client (CLAUDE.md)", check.stdout)
        before = self.claude_state() | {"CLAUDE.md": self.text("CLAUDE.md")}
        again = self.run_sync()
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertNotIn("sync: removed", again.stdout)
        self.assertEqual(before, self.claude_state() | {"CLAUDE.md": self.text("CLAUDE.md")})

    def test_check_names_each_leftover_alone_and_a_sync_removes_it(self):
        for part, rel in (("manifest", ".claude/skills/KIT_MANIFEST.json"), ("skills", ".claude/skills/investigate"),
                          ("pinned", f".claude/skills/{PINNED}"), ("kit_dir", ".claude/ai-kit"),
                          ("key", f".claude/settings.json enabledPlugins {PINNED}@skills-dir"),
                          ("hooks", ".claude/settings.json hooks that run .claude/ai-kit/hooks/")):
            with self.subTest(part=part):
                self.vendor("docs", parts=(part,), release=False)
                check = self.run_sync("--check")
                self.assertEqual(check.returncode, 1, check.stdout + check.stderr)
                self.assertIn(f"sync: vendored kit state left: {rel}: ", check.stdout)
                self.assertIn(f"sync: KIT-081 stage 2b removed the vendored mode: run platforms/tools/sync-project.sh"
                              f" {self.repo} once", check.stdout)
                other = [line for line in check.stdout.splitlines() if not line.startswith((
                    "sync: profile=docs (CLAUDE.md)", "sync: vendored kit state left: ", "sync: KIT-081 stage 2b"))]
                self.assertEqual(other, [], "the leftover alone fails the check")
                write = self.run_sync()
                self.assertEqual(write.returncode, 0, write.stdout + write.stderr)
                self.assertIn(f"sync: removed {rel}", write.stdout)
                check = self.run_sync("--check")
                self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    def test_unmarked_folders_and_symbolic_links_are_kept(self):
        outside = self.scratch()
        target = outside / "target"
        target.mkdir()
        (target / ".agent-rules-kit").write_text("marked\n")
        self.vendor("docs", parts=("manifest", "key"))  # the manifest names investigate and sdd-tasks
        skills = self.repo / ".claude" / "skills"
        (skills / "investigate").mkdir()  # the project's own folder under a name the manifest lists
        (skills / "investigate" / "SKILL.md").write_text("mine\n")
        (skills / PINNED).mkdir()
        (skills / PINNED / "notes.md").write_text("mine\n")
        (self.repo / ".claude" / "ai-kit").symlink_to(target)
        (skills / "sdd-tasks").symlink_to(target)
        write = self.run_sync()
        self.assertEqual(write.returncode, 0, write.stdout + write.stderr)
        for rel in (".claude/skills/investigate", f".claude/skills/{PINNED}", ".claude/ai-kit",
                    ".claude/skills/sdd-tasks"):
            self.assertIn(f"sync: kept {rel}: ", write.stdout)
        self.assertEqual((skills / "investigate" / "SKILL.md").read_text(), "mine\n")
        self.assertEqual((skills / PINNED / "notes.md").read_text(), "mine\n")
        self.assertTrue((self.repo / ".claude" / "ai-kit").is_symlink() and (skills / "sdd-tasks").is_symlink())
        self.assertTrue((target / ".agent-rules-kit").is_file())
        self.assertFalse((skills / "KIT_MANIFEST.json").exists())
        check = self.run_sync("--check")
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    def test_a_symbolic_skills_folder_is_never_read(self):
        outside = self.scratch()
        shutil.copytree(PLUGIN / "skills" / "investigate", outside / "investigate")
        self.mark(outside / "investigate", "plugins/guardrails/skills/investigate")
        (outside / "KIT_MANIFEST.json").write_text('{"profile": "godot", "skills": {"investigate": {}}}\n')
        (self.repo / ".claude" / "skills").symlink_to(outside)
        before = {p: p.read_bytes() for p in outside.rglob("*") if p.is_file()}
        for args in (("--check",), ()):
            result = self.run_sync(*args)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("sync: profile=docs (CLAUDE.md)", result.stdout)
        self.assertEqual(before, {p: p.read_bytes() for p in outside.rglob("*") if p.is_file()})
        (self.repo / "CLAUDE.md").write_text(self.claude_md(None))  # nor is the profile list read through it
        self.assertIn("sync: profile=docs (inferred)", self.run_sync("--check").stdout)

    def test_the_vendor_skills_flag_is_refused(self):
        before = self.claude_state() | {"CLAUDE.md": self.text("CLAUDE.md")}
        for args in (("--vendor-skills",), ("--check", "--vendor-skills"), ("--profile", "docs", "--vendor-skills")):
            with self.subTest(args=args):
                result = self.run_sync(*args)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertEqual(result.stderr.count("\n"), 1, result.stderr)
                self.assertIn("sync: --vendor-skills was removed in KIT-081 stage 2b: a project uses the installed"
                              " guardrails@ai-kit plugin", result.stderr)
        self.assertEqual(before, self.claude_state() | {"CLAUDE.md": self.text("CLAUDE.md")})

    def test_plugins_mode_keeps_the_kit_clone_as_the_fallback(self):  # B2: an unsynced or plugins-mode repo
        result = self.run_sync("--profile", "docs,godot:client")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        rule = (self.repo / ".claude" / "rules" / "guardrails-code.md").read_text()
        self.assertIn(HEAD_TOOL + "tools/complexity.py", rule)
        self.assertIn("~/.ai-kit/plugins/guardrails/skills/<skill>/references/<file>", rule)
        self.assertNotIn("guardrails-pinned", rule + (self.repo / "AGENTS.md").read_text())
        self.assertNotIn(PINNED_TOOL, "".join(self.vendored_texts().values()))

    def test_every_kit_tool_call_names_a_kit_file(self):  # B2; KIT-081 stage 1: the schemas folder too
        refs = {}
        for root in ("skills", "rules", "agents", "templates"):
            for path in (PLUGIN / root).rglob("*"):
                if path.is_file() and HEAD_TOOL.encode() in path.read_bytes():
                    self.assertEqual(path.suffix, ".md", f"{path} calls a kit tool outside markdown")
                    for m in re.finditer(re.escape(HEAD_TOOL) + r"([A-Za-z0-9_./-]+)", path.read_text()):
                        refs.setdefault(m.group(1).rstrip("."), path)
        self.assertTrue(refs)
        self.assertIn("ci/schemas", refs)  # the spec validators take the kit's schemas folder
        for rel, path in refs.items():
            target = KIT / "platforms" / rel
            self.assertTrue(target.is_file() or (rel == "ci/schemas" and target.is_dir()),
                            f"{path} calls ~/.ai-kit/platforms/{rel}")

    def test_plugins_mode_keeps_the_marketplace_plugin(self):
        enabled = self.settings()["enabledPlugins"]
        self.assertEqual({k: v for k, v in enabled.items() if "guardrails" in k}, {"guardrails@ai-kit": True})
        self.assertFalse(self.pinned().exists())
        self.assertFalse((self.repo / ".claude" / "ai-kit").exists())
        self.assertNotIn("hooks", self.settings())  # the plugin carries the hooks in plugins mode

    def test_agents_md_block_says_where_kit_skills_live(self):  # KIT-070: rules point at skill references
        (self.repo / "client").mkdir()
        result = self.run_sync("--profile", "docs,godot:client")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        client = self.text("client/AGENTS.md")
        self.assertIn("A kit skill or reference a rule names is in `~/.ai-kit/plugins/guardrails/skills/<skill>/`.",
                      client)
        self.assertNotIn(".claude/skills/", client)  # KIT-081 stage 2b: no project copy

    def test_rule_copy_says_where_kit_skills_live(self):  # review of PR #261 (N4): Claude can open the references
        (self.repo / "client").mkdir()
        result = self.run_sync("--profile", "docs,godot:client")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        lines = self.text(".claude/rules/guardrails-code.md").splitlines()
        marker = next(i for i, line in enumerate(lines) if line.startswith("<!-- agent-rules-kit: generated from"))
        self.assertEqual(lines[marker + 1], "Kit files this rule names: skill `<skill>`, reference `<file>` is"
                         " `~/.ai-kit/plugins/guardrails/skills/<skill>/references/<file>`.")  # KIT-081 stage 2b
        self.assertNotIn("Kit files this rule names:", self.text("client/AGENTS.md"))
        check = self.run_sync("--check", "--profile", "docs,godot:client")
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    def test_removed_kit_skill_citation_fails(self):  # KIT-070: a resync leaves no dangling skill citation
        for line in ("Detail: skill `godot-standards` § 3.",
                     "see `.claude/skills/protocol-contract/SKILL.md:41`",
                     "the `testing` § 6 table",
                     "preload guardrails:code-standards here",
                     "`plugins/guardrails/skills/persistence/references/redis-7.md`",
                     # review of PR #261: forms without backticks or the word "skill"
                     "run skill testing § 6 before done",
                     "a response/error (`protocol-contract`); a client FEAT contains no outcome rule",
                     "see `godot-standards/references/network-codec.md`",
                     "stress-test it with /grilling first",
                     "CHANGELOG entry (code-standards § 9)",
                     "the kit-generated skills `protocol-contract:41` and `session:40`",
                     "Skill `architecture` § 2 places it"):
            with self.subTest(line=line):
                self.write_md("docs/spec/decisions/DEC-002-x.md", "# DEC-002\n\n" + line + "\n")
                result = self.run_sync("--check")
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("removed kit skill: docs/spec/decisions/DEC-002-x.md:3", result.stdout)
                self.assertIn("KIT-070", result.stdout)

    def test_each_removed_skill_form_alone_fails(self):  # review round 2: each input matches exactly one form
        for line in ("Detail: skill testing, then review.",                     # skill x
                     "the testing skill decides",                               # x skill
                     "the `testing` § 6 table",                                 # x § n
                     "preload guardrails:testing here",                         # guardrails:x
                     "`plugins/guardrails/skills/testing/` holds it",           # skills/x/
                     "see `testing/references/gates.md`",                       # x/references/
                     "stress-test it with /grilling first",                     # /x
                     "a response/error (`protocol-contract`); a client FEAT"):  # a hyphenated name
            with self.subTest(line=line):
                self.write_md("docs/forms.md", line + "\n")
                result = self.run_sync("--check")
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("removed kit skill: docs/forms.md:1:", result.stdout)

    def test_removed_skill_scan_crash_fails_the_check(self):  # review round 2: a crashed scan is never a clean one
        outside = tempfile.TemporaryDirectory()  # self.tmp is the fixture repo itself
        self.addCleanup(outside.cleanup)
        fake = Path(outside.name)
        real = shutil.which("python3")
        (fake / "python3").write_text("#!/bin/bash\n"
                                      'if [[ "$1" == - && "$3" == *code-standards* ]]; then exit 3; fi\n'
                                      f'exec "{real}" "$@"\n')
        (fake / "python3").chmod(0o755)
        result = self.run_sync("--check", env={"PATH": f"{fake}{os.pathsep}{os.environ['PATH']}"})
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("sync: removed-skill scan failed", result.stdout + result.stderr)

    def test_removed_skill_scan_reports_non_ascii_lines(self):  # review round 2: no UnicodeEncodeError, no lost files
        self.write_md("docs/arrow.md", "skill testing § 6 → test-gates.md\n")
        self.write_md("docs/zzz.md", "Detail: skill testing, then review.\n")
        for env in ({"PYTHONIOENCODING": "ascii"}, {"LC_ALL": "en_US.ISO8859-1"}):
            with self.subTest(env=env):
                result = self.run_sync("--check", env=env)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("removed kit skill: docs/arrow.md:1:", result.stdout)
                self.assertIn("removed kit skill: docs/zzz.md:1:", result.stdout)

    def test_removed_skill_scan_reports_a_non_utf8_file_name(self):  # review round 2
        try:
            (self.repo / "docs").mkdir(exist_ok=True)
            with open(os.path.join(os.fsencode(self.repo / "docs"), b"x\xff.md"), "w", encoding="utf-8") as handle:
                handle.write("Detail: skill testing, then review.\n")
        except OSError:
            self.skipTest("this file system refuses a file name that is not UTF-8")
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("removed kit skill: docs/x", result.stdout)

    def test_removed_kit_skill_scan_has_no_false_positives(self):  # KIT-070
        self.write_md("docs/notes.md", "Our testing strategy follows the architecture of the persistence layer.\n"
                      "skill `sdd-implement`, reference `testing-notes.md`; grilling session; `java-standards-v2`\n"
                      "pentesting and load-testing notes; the asset-importer tool; `src/testing/fixtures`\n"
                      "unit testing skills; its own grilling and DEC session; `docs/architecture/overview.md`\n")
        self.write_md("docs/spec/decisions/DEC-003-x.md",
                      "# DEC-003\n\nskill `godot-standards` (history) <!-- kit-path-ok -->\n")
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


SPEC_MD = """---
project: "fixture"
version: "0.1.0"
updated: "2026-11-14"
{extra}---

# Fixture
"""

BLOCK_BEGIN = "<!-- agent-rules-kit: path rules begin"
BLOCK_END = "<!-- agent-rules-kit: path rules end -->"


def rule_bullet(name):
    """The first always/never bullet of the kit rule, a line its AGENTS.md block must carry."""
    body = (KIT / "plugins" / "guardrails" / "rules" / f"{name}.md").read_text().split("\n---\n", 1)[1]
    return next(line for line in body.splitlines() if line.startswith("- "))


if __name__ == "__main__":
    unittest.main()
