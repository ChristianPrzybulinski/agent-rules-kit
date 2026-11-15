"""sync-project.sh --check: stale kit path scan on a throwaway repo."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent.parent / "tools" / "sync-project.sh"
KIT = SCRIPT.parents[2]
VERSION = (KIT / "VERSION").read_text(encoding="utf-8").strip()
MAP = KIT / "platforms" / "tools" / "sync-profiles.txt"  # KIT-047: one plugin, the map picks the copies
PLUGIN = KIT / "plugins" / "guardrails"
PINNED = "guardrails-pinned"  # KIT-072: the project's pinned copy of the plugin, a skills-directory plugin
KIT_SKILLS = sorted(p.name for p in (PLUGIN / "skills").iterdir() if (p / "SKILL.md").is_file())

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
        # KIT-072: AI_KIT_CLAUDE_PROBE=1 makes --check ask the claude CLI which plugins load; a test opts in with a stub
        full = dict(os.environ, AI_KIT_CLAUDE_PROBE="0")
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
            f"<!-- generated by agent-rules-kit sync-project.sh v{VERSION};"
            " AGENTS.md is the source -->",
            "@AGENTS.md"])
        data = json.loads(settings.read_text())
        self.assertEqual(data["extraKnownMarketplaces"]["ai-kit"],
                         {"source": {"source": "github",
                                     "repo": "ChristianPrzybulinski/agent-rules-kit"}})
        ai_kit = {k for k in data["enabledPlugins"] if k.endswith("@ai-kit")}
        self.assertEqual(ai_kit, {"guardrails@ai-kit"})
        self.assertTrue(all(data["enabledPlugins"][k] is True for k in ai_kit))
        self.assertIs(data["includeGitInstructions"], False)  # KIT-071
        before = (claude.read_bytes(), settings.read_bytes())
        second = self.run_sync()
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertEqual(before, (claude.read_bytes(), settings.read_bytes()))

    def test_spec_lint_copies_the_task_schema(self):  # KIT-068: tracker none keeps docs/spec/tasks/
        copied = self.repo / ".github" / "spec-lint" / "schemas" / "task.schema.json"
        self.assertEqual(copied.read_bytes(), (KIT / "platforms" / "ci" / "schemas" / "task.schema.json").read_bytes())

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
            self.assertFalse((repo / ".github" / "spec-lint").exists())

    def kit_skills(self, profiles):
        """Skills that sync-profiles.txt sends to any of the profiles; "-" (never vendored) matches "-"."""
        names = []
        for line in MAP.read_text().splitlines():
            if line.startswith("skills/"):
                entry, receivers = (part.strip() for part in line.split("|"))
                if set(receivers.split()) & set(profiles):
                    names.append(entry.split("/", 1)[1])
        return sorted(names)

    def vendor_install(self, *args):
        result = self.run_sync("--vendor-skills", *args)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_vendor_skills_install(self):
        skills = self.kit_skills({"docs"})
        own = self.repo / ".claude" / "skills" / "review-loop"
        own.mkdir(parents=True)
        (own / "SKILL.md").write_text("mine\n")
        result = self.vendor_install()
        self.assertIn("sync: skills=vendored", result.stdout)
        root = self.repo / ".claude" / "skills"
        marked = {p.parent.name for p in root.glob("*/.agent-rules-kit")}
        self.assertEqual(marked - {PINNED}, set(skills))  # KIT-072: the pinned plugin copy is marked too
        manifest = json.loads((root / "KIT_MANIFEST.json").read_text())
        kit_files = sum(f.is_file() for name in skills
                        for f in (KIT / "plugins" / "guardrails" / "skills" / name).rglob("*"))
        self.assertEqual((manifest["KIT_VERSION"], manifest["profile"]), (VERSION, "docs"))
        self.assertEqual(len(manifest["skills"]), len(skills))
        self.assertEqual(sum(len(s["files"]) for s in manifest["skills"].values()),
                         kit_files + len(skills))
        for name in skills:
            kit_dir = KIT / "plugins" / "guardrails" / "skills" / name
            want = {f.relative_to(kit_dir) for f in kit_dir.rglob("*") if f.is_file()}
            got = {f.relative_to(root / name) for f in (root / name).rglob("*") if f.is_file()}
            self.assertEqual(got - want, {Path(".agent-rules-kit")}, name)
            self.assertEqual(want - got, set(), name)
        self.assertEqual((own / "SKILL.md").read_text(), "mine\n")
        settings = json.loads((self.repo / ".claude" / "settings.json").read_text())
        self.assertEqual({k for k in settings["enabledPlugins"] if k.endswith("@ai-kit")},
                         {"guardrails@ai-kit"})
        for name in self.kit_skills({"-"}):  # always on: loads from the plugin, so never vendored too
            self.assertFalse((root / name).exists(), name)

    def test_vendor_skills_idempotent_and_check_passes(self):
        self.vendor_install()
        def state():
            return {f: f.read_bytes() for f in (self.repo / ".claude").rglob("*") if f.is_file()}
        before = state()
        second = self.run_sync()  # no flag: the manifest keeps the vendored mode
        self.assertIn("sync: skills=vendored", second.stdout)
        self.assertEqual(before, state())
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_vendor_skills_check_detects_drift(self):
        self.vendor_install()
        name = self.kit_skills({"docs"})[0]
        with (self.repo / ".claude" / "skills" / name / "SKILL.md").open("a") as fh:
            fh.write("x")
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("diverges from the manifest", result.stdout)
        self.assertEqual(self.run_sync().returncode, 0)  # resync restores the copy
        (self.repo / ".claude" / "skills" / name / "extra.txt").write_text("x\n")
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("not in manifest", result.stdout)

    def test_vendor_skills_profile_switch(self):
        self.vendor_install("--profile", "docs,godot")
        root = self.repo / ".claude" / "skills"
        kept = self.kit_skills({"godot"})[0]  # in both profiles, so rewritten whole
        (root / kept / "extra.txt").write_text("x\n")
        (root / "review-loop").mkdir()
        (root / "review-loop" / "SKILL.md").write_text("mine\n")
        result = self.run_sync("--profile", "godot")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((root / "sdd-tasks").exists())
        self.assertTrue((root / "investigate" / "SKILL.md").is_file())
        self.assertFalse((root / kept / "extra.txt").exists())
        self.assertEqual((root / "review-loop" / "SKILL.md").read_text(), "mine\n")
        check = self.run_sync("--check", "--profile", "godot")
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

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

    def test_manifest_profile_list_is_sticky(self):  # KIT-017
        self.vendor_install("--profile", "docs,godot:client,java:server")
        before = self.claude_state()
        check = self.run_sync("--check")
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        self.assertIn("sync: profile=docs,godot:client,java:server (manifest)", check.stdout)
        write = self.run_sync()
        self.assertEqual(write.returncode, 0, write.stdout + write.stderr)
        self.assertIn("sync: profile=docs,godot:client,java:server (manifest)", write.stdout)
        self.assertIn("[0 written, 0 removed]", write.stdout)
        self.assertNotIn("sync: removed", write.stdout)
        self.assertEqual(before, self.claude_state())

    def test_explicit_profile_overrides_manifest(self):  # KIT-017
        self.vendor_install("--profile", "docs,godot:client,java:server")
        check = self.run_sync("--check", "--profile", "docs")
        self.assertEqual(check.returncode, 1)
        self.assertIn("sync: profile=docs (--profile)", check.stdout)
        self.assertIn("profile='docs,godot:client,java:server' expected 'docs'", check.stdout)
        write = self.run_sync("--profile", "docs")
        self.assertEqual(write.returncode, 0, write.stdout + write.stderr)
        self.assertIn("sync: removed .claude/skills/investigate (not in profile)", write.stdout)
        self.assertFalse((self.repo / ".claude" / "rules" / "guardrails-godot.md").exists())
        manifest = json.loads((self.repo / ".claude" / "skills" / "KIT_MANIFEST.json").read_text())
        self.assertEqual(manifest["profile"], "docs")
        bare = self.run_sync("--check")
        self.assertEqual(bare.returncode, 0, bare.stdout + bare.stderr)
        self.assertIn("sync: profile=docs (manifest)", bare.stdout)

    def test_manifest_without_valid_profile(self):  # KIT-017
        self.vendor_install()
        path = self.repo / ".claude" / "skills" / "KIT_MANIFEST.json"
        manifest = json.loads(path.read_text())
        del manifest["profile"]
        path.write_text(json.dumps(manifest))
        result = self.run_sync("--check")  # no recorded list: inference decides
        self.assertIn("sync: profile=docs (inferred)", result.stdout)
        manifest["profile"] = "docs,rust"
        path.write_text(json.dumps(manifest))
        before = self.claude_state()
        result = self.run_sync()
        self.assertEqual(result.returncode, 2)
        self.assertIn("KIT_MANIFEST.json records that profile; pass --profile", result.stderr)
        self.assertEqual(before, self.claude_state())

    def test_vendor_skills_collision_refusal(self):
        with tempfile.TemporaryDirectory() as other:
            repo = Path(other)
            (repo / "AGENTS.md").write_text("# x\n")
            (repo / "project.godot").write_text("")
            (repo / ".claude" / "skills" / "investigate").mkdir(parents=True)
            result = self.run_sync("--vendor-skills", repo=repo)
            self.assertEqual(result.returncode, 1)
            self.assertIn("is not generated", result.stdout + result.stderr)
            self.assertFalse((repo / ".claude" / "skills" / "KIT_MANIFEST.json").exists())
            self.assertFalse((repo / ".claude" / "settings.json").exists())
            self.assertFalse((repo / ".github" / "spec-lint").exists())

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

    def test_agents_md_skips_a_missing_folder(self):
        result = self.run_sync("--profile", "docs,godot:client")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.repo / "client").exists(), "the sync creates no folder")
        check = self.run_sync("--check", "--profile", "docs,godot:client")
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    # KIT-067 review fix round: the block never leaves the repository, keeps the text around it and skips nested
    # checkouts; a rule_paths entry that does nothing says so.

    def outside_dir(self):
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside)
        return outside

    def root_block(self):
        text = self.text("AGENTS.md")
        return text[text.index(BLOCK_BEGIN):text.index(BLOCK_END) + len(BLOCK_END)]

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

    def test_agents_md_refuses_a_folder_reached_through_a_symlink(self):
        """Two targets that resolve to one real folder (docs/link -> ../client) would rewrite each other forever."""
        (self.repo / "client").mkdir()
        os.symlink("../client", self.repo / "docs" / "link")
        self.spec_md("sdd:\n  rule_paths: {json: [docs/link]}\n")
        message = "sync: docs/link goes through a symbolic link; the sync writes no path-rule block there"
        for args in ((), ("--check",)):
            result = self.run_sync(*args, "--profile", "docs,godot:client")
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn(message, result.stdout)
        self.assertFalse((self.repo / "client" / "AGENTS.md").exists())

    def test_agents_md_keeps_the_dominant_line_ending(self):
        (self.repo / "AGENTS.md").write_bytes(b"# x\n\nLF line.\nCRLF line.\r\n")
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = (self.repo / "AGENTS.md").read_bytes()
        self.assertTrue(data.startswith(b"# x\n\nLF line.\n"), data[:40])
        self.assertNotIn(b"\r", data[data.index(BLOCK_BEGIN.encode()):], "the block takes the dominant LF ending")

    def test_agents_md_refuses_a_symlinked_agents_md(self):
        outside = self.outside_dir()
        (outside / "AGENTS.md").write_text("# outside\n")
        (self.repo / "client").mkdir()
        os.symlink(outside / "AGENTS.md", self.repo / "client" / "AGENTS.md")
        result = self.run_sync("--profile", "docs,godot:client")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("sync: client/AGENTS.md is a symbolic link; the sync writes no path-rule block through it",
                      result.stdout)
        self.assertEqual((outside / "AGENTS.md").read_text(), "# outside\n")

    def test_agents_md_refuses_broken_markers(self):
        broken = "# x\n\n" + self.root_block().replace(BLOCK_END, "") + "\n"
        (self.repo / "AGENTS.md").write_text(broken)
        message = "sync: AGENTS.md path-rule block markers are broken"
        for args in ((), ("--check",)):
            result = self.run_sync(*args)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn(message, result.stdout)
        self.assertEqual(self.text("AGENTS.md"), broken)

    def test_agents_md_skips_a_nested_checkout(self):
        nested = self.repo / "vendor" / "lib"
        nested.mkdir(parents=True)
        (nested / ".git").write_text("gitdir: /elsewhere/.git/modules/lib\n")
        foreign = "# lib\n\n" + self.root_block() + "\n"
        (nested / "AGENTS.md").write_text(foreign)
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((nested / "AGENTS.md").read_text(), foreign, "a nested checkout's block is its own")
        check = self.run_sync("--check")
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    def test_agents_md_keeps_crlf_line_endings(self):
        (self.repo / "AGENTS.md").write_bytes(b"# x\r\n\r\nHand-written line.\r\n")
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = (self.repo / "AGENTS.md").read_bytes()
        self.assertTrue(data.startswith(b"# x\r\n\r\nHand-written line.\r\n\r\n" + BLOCK_BEGIN.encode()), data[:80])
        self.assertNotIn(b"\n", data.replace(b"\r\n", b""), "every line ends in CRLF")
        check = self.run_sync("--check")
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        self.assertEqual(self.run_sync().returncode, 0)
        self.assertEqual(data, (self.repo / "AGENTS.md").read_bytes())

    def test_agents_md_block_removal_keeps_the_blank_line(self):
        (self.repo / "AGENTS.md").write_text("# x\n\n" + self.root_block() + "\n\n## After\n\ntext\n")
        (self.repo / "game" / "protocol").mkdir(parents=True)
        self.spec_md("sdd:\n  rule_paths: {json: [game/protocol], protocol: [game]}\n")
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.text("AGENTS.md"), "# x\n\n## After\n\ntext\n")

    def test_rule_paths_for_a_rule_outside_the_profile_warns(self):
        self.spec_md("sdd:\n  rule_paths: {godot: [client]}\n")
        result = self.run_sync("--profile", "docs")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("sync: warning: sdd.rule_paths.godot does nothing: profile docs receives no rules/godot.md",
                      result.stderr)

    def test_rule_paths_into_a_skipped_folder_warns(self):
        (self.repo / "build" / "gen").mkdir(parents=True)
        self.spec_md("sdd:\n  rule_paths: {json: [build/gen]}\n")
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("sync: warning: build/gen is inside a folder the AGENTS.md scan skips", result.stderr)
        self.assertIn(rule_bullet("json"), self.text("build/gen/AGENTS.md"))

    # KIT-072: a vendored project pins the whole kit. .claude/ai-kit/hooks/ carries the kit hooks, which
    # .claude/settings.json runs; the plugin copy under .claude/skills/guardrails-pinned/ carries the agents and every
    # skill the profile does not copy as a plain skill; guardrails@ai-kit, which follows the kit head, is off.

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

    def kit_hooks(self):
        """The kit hooks as {event: [(matcher, timeout, command)]}, from plugins/guardrails/hooks/hooks.json."""
        hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text())["hooks"]
        return {event: [(group.get("matcher"), hook.get("timeout"), hook["command"])
                        for group in groups for hook in group["hooks"]] for event, groups in hooks.items()}

    def settings_hooks(self):
        """The settings hooks as {event: [(matcher, timeout, script text)]}, each command resolved in the repo."""
        found = {}
        for event, groups in self.settings().get("hooks", {}).items():
            for group in groups:
                for hook in group["hooks"]:
                    command = hook["command"]
                    self.assertTrue(command.startswith('bash "${CLAUDE_PROJECT_DIR}/.claude/ai-kit/hooks/'), command)
                    script = self.repo / command.split("${CLAUDE_PROJECT_DIR}/", 1)[1].rstrip('"')
                    found.setdefault(event, []).append((group.get("matcher"), hook.get("timeout"),
                                                        script.read_text()))
        return found

    def test_vendored_mode_pins_the_plugin(self):
        for profile in ("docs", "godot", "docs,godot:client,java:server,python:platform"):
            with self.subTest(profile=profile):
                self.vendor_install("--profile", profile)
                plain = set(self.kit_skills(set(p.split(":")[0] for p in profile.split(","))))
                copied = {p.name for p in self.pinned("skills").iterdir()}
                self.assertEqual(copied, set(KIT_SKILLS) - plain)  # each kit skill lists once
                for name in self.kit_skills({"-"}):
                    self.assertIn(name, copied)
                manifest_plugin = json.loads(self.pinned(".claude-plugin/plugin.json").read_text())
                self.assertEqual((manifest_plugin["name"], manifest_plugin["version"]), (PINNED, VERSION))
                hooks = self.settings_hooks()  # every kit hook runs from settings, verbatim, with its matcher
                self.assertEqual({e: [(m, t) for m, t, _ in h] for e, h in hooks.items()},
                                 {e: [(m, t) for m, t, _ in h] for e, h in self.kit_hooks().items()})
                for event, entries in self.kit_hooks().items():
                    for (_, _, script), (_, _, command) in zip(hooks[event], entries):
                        self.assertTrue(script.endswith("\n" + command + "\n"), event)
                for gone in ("hooks", "AGENTS.md", "INDEX.md", "evals", "rules", "plugin.json", ".devin-plugin"):
                    self.assertFalse(self.pinned(gone).exists(), gone)
                self.assertTrue(self.pinned("templates").is_dir())
                self.assertIn(f"plugins/guardrails kit {VERSION} generated by platforms/tools/sync-project.sh",
                              self.pinned(".agent-rules-kit").read_text())
                enabled = self.settings()["enabledPlugins"]
                self.assertIs(enabled["guardrails@ai-kit"], False)
                self.assertIs(enabled[f"{PINNED}@skills-dir"], True)
                manifest = json.loads((self.repo / ".claude" / "skills" / "KIT_MANIFEST.json").read_text())
                self.assertNotIn(PINNED, manifest["skills"])
                self.assertRegex(manifest["KIT_COMMIT"], r"^([0-9a-f]{40}(-dirty)?)?$")
                files = {str(p.relative_to(self.pinned())) for p in self.pinned().rglob("*") if p.is_file()}
                self.assertEqual(set(manifest["plugin"]["files"]), files)
                self.assertEqual(manifest["plugin"]["name"], PINNED)
                kit_dir = self.repo / ".claude" / "ai-kit"
                files = {str(p.relative_to(kit_dir)) for p in kit_dir.rglob("*") if p.is_file()}
                self.assertEqual(set(manifest["kit_dir"]["files"]), files)
                check = self.run_sync("--check", "--profile", profile)
                self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    def test_pinned_agents_name_skills_that_resolve(self):
        # The kit agents preload only always-on skills since KIT-070; a fixture preload of investigate, copied plain
        # for godot and pinned for docs, keeps both renames covered.
        kit = self.scratch() / "kit-agents"
        shutil.copytree(KIT, kit, ignore=shutil.ignore_patterns(".git", "evals"))
        agent = kit / "plugins" / "guardrails" / "agents" / "reviewer.md"
        text = agent.read_text()
        self.assertIn("  - guardrails:review\n", text)
        agent.write_text(text.replace("  - guardrails:review\n", "  - guardrails:review\n  - guardrails:investigate\n", 1))
        script = kit / "platforms" / "tools" / "sync-project.sh"
        for profile, investigate in (("docs", f"{PINNED}:investigate"), ("godot", "investigate")):
            with self.subTest(profile=profile):
                result = self.run_kit(script, "--vendor-skills", "--profile", profile)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                text = self.pinned("agents/reviewer.md").read_text()
                self.assertIn(f"  - {PINNED}:review\n", text)
                self.assertIn(f"  - {investigate}\n", text)
                for agent in self.pinned("agents").iterdir():
                    self.assertNotIn("guardrails:", agent.read_text(), agent.name)

    def test_pinned_plugin_check_flags_drift(self):
        self.vendor_install()
        with self.pinned("agents/reviewer.md").open("a") as fh:
            fh.write(" ")
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"sync: .claude/skills/{PINNED}/agents/reviewer.md diverges from the manifest", result.stdout)
        self.assertEqual(self.run_sync().returncode, 0)  # resync restores the copy
        self.pinned("agents/extra.md").write_text("x\n")
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"sync: .claude/skills/{PINNED}/agents/extra.md not in manifest", result.stdout)
        self.assertEqual(self.run_sync().returncode, 0)
        self.assertFalse(self.pinned("agents/extra.md").exists())
        script = next((self.repo / ".claude" / "ai-kit" / "hooks").glob("PreToolUse-0-0.sh"))
        with script.open("a") as fh:
            fh.write("exit 0\n")
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("sync: .claude/ai-kit/hooks/PreToolUse-0-0.sh diverges from the manifest", result.stdout)
        self.assertEqual(self.run_sync().returncode, 0)
        data = self.settings()
        del data["hooks"]["PreToolUse"]
        self.write_settings(data)
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("hooks: want the kit hooks of .claude/ai-kit/hooks/hooks.json", result.stdout)

    def test_settings_hooks_run_the_kit_hooks_beside_the_projects_own(self):
        own = {"matcher": "Bash", "hooks": [{"type": "command", "command": "echo own"}]}
        self.write_settings(dict(self.settings(), hooks={"PreToolUse": [own], "Stop": [own]}))
        self.vendor_install()
        first = (self.repo / ".claude" / "settings.json").read_text()
        self.assertEqual(self.run_sync().returncode, 0)
        self.assertEqual((self.repo / ".claude" / "settings.json").read_text(), first)  # idempotent, no duplicate
        hooks = self.settings()["hooks"]
        self.assertEqual(hooks["Stop"], [own])
        self.assertEqual(hooks["PreToolUse"][0], own)
        self.assertEqual(len(hooks["PreToolUse"]), 1 + len(json.loads(
            (PLUGIN / "hooks" / "hooks.json").read_text())["hooks"]["PreToolUse"]))
        # the settings command runs the kit hook verbatim: same verdict as the kit command on the same input
        kit = json.loads((PLUGIN / "hooks" / "hooks.json").read_text())["hooks"]["PreToolUse"]
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.repo))
        for command in ("git push --force origin main", "ls"):
            payload = json.dumps({"cwd": str(self.repo), "tool_name": "Bash", "tool_input": {"command": command}})
            for group, entry in zip(kit, hooks["PreToolUse"][1:]):
                want = subprocess.run(["bash", "-c", group["hooks"][0]["command"]], input=payload, cwd=self.repo,
                                      capture_output=True, text=True, env=env, check=False)
                got = subprocess.run(["bash", "-c", entry["hooks"][0]["command"]], input=payload, cwd=self.repo,
                                     capture_output=True, text=True, env=env, check=False)
                self.assertEqual((got.returncode, got.stdout, got.stderr),
                                 (want.returncode, want.stdout, want.stderr), command)
        self.assertNotEqual(subprocess.run(  # the guard still blocks
            ["bash", "-c", hooks["PreToolUse"][1]["hooks"][0]["command"]], cwd=self.repo, env=env, text=True,
            input=json.dumps({"cwd": str(self.repo), "tool_input": {"command": "git push --force origin main"}}),
            capture_output=True, check=False).returncode, 0)
        # plugins mode takes the kit hooks and the pinned key out again and keeps the project's own
        (self.repo / ".claude" / "skills" / "KIT_MANIFEST.json").unlink()
        self.assertEqual(self.run_sync().returncode, 0)
        data = self.settings()
        self.assertEqual(data["hooks"], {"PreToolUse": [own], "Stop": [own]})
        self.assertEqual({k: v for k, v in data["enabledPlugins"].items() if "guardrails" in k},
                         {"guardrails@ai-kit": True})
        self.assertFalse((self.repo / ".claude" / "ai-kit").exists())
        self.assertFalse(self.pinned().exists())

    def test_vendored_sync_drops_retired_kit_plugins(self):  # review of c394007: base drops every other @ai-kit key
        data = self.settings()
        data["enabledPlugins"].update({"dev-core@ai-kit": True, "other@market": True})
        self.write_settings(data)
        self.vendor_install()
        enabled = self.settings()["enabledPlugins"]
        self.assertNotIn("dev-core@ai-kit", enabled)
        self.assertIs(enabled["other@market"], True)
        first = (self.repo / ".claude" / "settings.json").read_text()
        check = self.run_sync("--check")
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        self.assertEqual(self.run_sync().returncode, 0)
        self.assertEqual((self.repo / ".claude" / "settings.json").read_text(), first)  # stable from the first sync

    def test_a_settings_shape_the_pin_cannot_merge_is_refused(self):  # exit 2 before any write, no traceback
        good = self.settings()
        path = self.repo / ".claude" / "settings.json"
        for extra, message in (({"hooks": {"PreToolUse": {}}}, '"hooks" is not an object of event lists'),
                               ({"enabledPlugins": []}, '"enabledPlugins" is not an object')):
            with self.subTest(extra=extra):
                self.write_settings(dict(good, **extra))
                before = path.read_text()
                result = self.run_sync("--vendor-skills")
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn(f"sync: {path} {message}; fix it by hand", result.stdout)
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse(self.pinned().exists())
                self.assertFalse((self.repo / ".claude" / "skills" / "KIT_MANIFEST.json").exists())
                self.assertEqual(path.read_text(), before)
        self.write_settings(dict(good, hooks=["mine"]))  # plugins mode leaves a hooks value it cannot read alone
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.settings()["hooks"], ["mine"])

    def broken_kit(self):
        """A kit copy whose hooks.json does not parse, so the pin's write fails."""
        kit = self.scratch() / "broken-kit"
        shutil.copytree(KIT, kit, ignore=shutil.ignore_patterns(".git", "evals"))
        (kit / "plugins" / "guardrails" / "hooks" / "hooks.json").write_text("{")
        return kit / "platforms" / "tools" / "sync-project.sh"

    def test_a_failed_pin_write_turns_nothing_off(self):  # should-fix 1: the head goes off only after the copy
        script = self.broken_kit()
        result = self.run_kit(script, "--vendor-skills")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("in build_kit_dir", result.stderr)  # it failed in the pin's write, after the plain copies
        plain = self.repo / ".claude" / "skills" / self.kit_skills({"docs"})[0]
        self.assertTrue((plain / ".agent-rules-kit").is_file())
        data = self.settings()
        self.assertIs(data["enabledPlugins"].get("guardrails@ai-kit"), True)
        self.assertNotIn(f"{PINNED}@skills-dir", data["enabledPlugins"])
        self.assertNotIn("hooks", data)
        self.assertFalse(self.pinned().exists())
        self.assertFalse((self.repo / ".claude" / "ai-kit").exists())
        self.assertEqual(list((self.repo / ".claude").glob(".kit-pin-*")), [])
        # a pinned repo keeps its previous pin whole: the copy, the hooks and the head off
        self.vendor_install()
        before = {p: p.read_bytes() for p in (self.repo / ".claude").rglob("*") if p.is_file()}
        self.assertNotEqual(self.run_kit(script).returncode, 0)
        after = {p: p.read_bytes() for p in (self.repo / ".claude").rglob("*") if p.is_file()}
        self.assertEqual(after, before)

    def test_a_symlinked_pin_folder_is_refused_and_kept(self):  # should-fix 1: no rmtree through a link
        for rel in (f"skills/{PINNED}", "ai-kit"):
            with self.subTest(rel=rel), tempfile.TemporaryDirectory() as other:
                repo = Path(other) / "repo"
                (repo / "docs" / "spec").mkdir(parents=True)
                (repo / "AGENTS.md").write_text("# x\n")
                target = Path(other) / "target"
                target.mkdir()
                (target / ".agent-rules-kit").write_text("marked\n")
                link = repo / ".claude" / rel
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(target)
                result = self.run_sync("--vendor-skills", repo=repo)
                self.assertEqual(result.returncode, 1)
                self.assertIn(f"{link} is a symbolic link", result.stdout)
                self.assertNotIn("Traceback", result.stderr)
                self.assertTrue((target / ".agent-rules-kit").is_file())
                self.assertTrue(link.is_symlink())
                plugins = self.run_sync(repo=repo)  # plugins mode removes only real marked folders
                self.assertEqual(plugins.returncode, 0, plugins.stdout + plugins.stderr)
                self.assertTrue((target / ".agent-rules-kit").is_file())

    def test_check_flags_the_head_plugin_beside_the_pin(self):
        self.vendor_install()
        data = self.settings()
        data["enabledPlugins"]["guardrails@ai-kit"] = True
        self.write_settings(data)
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("guardrails@ai-kit: want false", result.stdout)
        self.assertEqual(self.run_sync().returncode, 0)
        self.write_settings({"enabledPlugins": {"guardrails@ai-kit": True}}, "settings.local.json")
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("sync: .claude/settings.local.json enables guardrails@ai-kit, which loads the kit head"
                      " beside the pin", result.stdout)
        self.write_settings({"enabledPlugins": {f"{PINNED}@skills-dir": False}}, "settings.local.json")
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"sync: .claude/settings.local.json turns off {PINNED}@skills-dir", result.stdout)

    def claude_stub(self, plugins):
        """A claude CLI that prints this plugin list; returns the env that puts it first on PATH."""
        bin_dir = self.scratch() / "stub-bin"
        bin_dir.mkdir(exist_ok=True)
        stub = bin_dir / "claude"
        stub.write_text("#!/bin/sh\n[ \"$1 $2 $3\" = 'plugin list --json' ] || exit 2\ncat <<'EOF'\n"
                        + json.dumps(plugins) + "\nEOF\n")
        stub.chmod(0o755)
        return {"PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}", "AI_KIT_CLAUDE_PROBE": "1", "CI": ""}

    def test_check_reads_the_active_plugins_from_claude(self):
        self.vendor_install()
        head = {"id": "guardrails@ai-kit", "scope": "user", "enabled": False, "version": VERSION}
        pinned = {"id": f"{PINNED}@skills-dir", "scope": "project", "enabled": True, "version": VERSION}
        ok = self.run_sync("--check", env=self.claude_stub([head, pinned]))
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        self.assertIn(f"sync: claude loads {PINNED}@skills-dir {VERSION} here", ok.stdout)
        result = self.run_sync("--check", env=self.claude_stub([dict(head, enabled=True), pinned]))
        self.assertEqual(result.returncode, 1)
        self.assertIn("sync: claude loads guardrails@ai-kit here, the kit head beside the pin", result.stdout)
        failed = dict(pinned, enabled=False, errors=["Not loaded — the name is already taken"])
        result = self.run_sync("--check", env=self.claude_stub([head, failed]))
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"sync: claude does not load {PINNED}@skills-dir: Not loaded — the name is already taken",
                      result.stdout)
        result = self.run_sync("--check", env=self.claude_stub([head, dict(pinned, version="0.0.1")]))
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"sync: claude loads {PINNED}@skills-dir 0.0.1, kit version {VERSION}", result.stdout)
        untrusted = self.run_sync("--check", env=self.claude_stub([head]))  # B1: no pinned plugin listed fails
        self.assertEqual(untrusted.returncode, 1)
        self.assertIn(f"sync: claude lists no {PINNED}@skills-dir here: accept the trust dialog at the main checkout"
                      " root", untrusted.stdout)
        skipped = self.run_sync("--check", env=dict(self.claude_stub([head]), AI_KIT_CLAUDE_PROBE=""))
        self.assertEqual(skipped.returncode, 0, skipped.stdout + skipped.stderr)  # the probe is opt-in
        self.assertNotIn("sync: claude", skipped.stdout)

    def test_pinned_plugin_collision_refusal(self):
        with tempfile.TemporaryDirectory() as other:
            repo = Path(other)
            (repo / "AGENTS.md").write_text("# x\n")
            (repo / "docs" / "spec").mkdir(parents=True)
            own = repo / ".claude" / "skills" / PINNED
            own.mkdir(parents=True)
            (own / "notes.md").write_text("mine\n")
            result = self.run_sync("--vendor-skills", repo=repo)
            self.assertEqual(result.returncode, 1)
            self.assertIn(f"{PINNED} exists and is not generated", result.stdout + result.stderr)
            self.assertEqual((own / "notes.md").read_text(), "mine\n")
            self.assertFalse((repo / ".claude" / "settings.json").exists())

    def test_resync_pins_a_vendored_repo_from_before_the_pin(self):  # the KIT-072 migration
        self.vendor_install()
        shutil.rmtree(self.pinned())
        shutil.rmtree(self.repo / ".claude" / "ai-kit")
        manifest_path = self.repo / ".claude" / "skills" / "KIT_MANIFEST.json"
        manifest = json.loads(manifest_path.read_text())
        for key in ("plugin", "kit_dir", "KIT_COMMIT", "copies"):
            manifest.pop(key)
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        data = self.settings()
        data["enabledPlugins"] = {"guardrails@ai-kit": True}
        del data["hooks"]
        self.write_settings(data)
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"sync: .claude/skills/{PINNED} missing: the kit plugin is not pinned (rerun sync-project.sh)",
                      result.stdout)
        self.assertEqual(self.run_sync().returncode, 0)  # a bare resync keeps the vendored mode and pins
        self.assertTrue(self.pinned(".claude-plugin/plugin.json").is_file())
        self.assertIs(self.settings()["enabledPlugins"]["guardrails@ai-kit"], False)
        self.assertEqual(set(self.settings_hooks()), set(self.kit_hooks()))
        check = self.run_sync("--check")
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    def kit_with_fake_spec_lint_file(self):
        """A kit copy whose kit_files() lists one more spec-lint file, as a later kit change would add one."""
        kit = self.scratch() / "kit-copy"
        shutil.copytree(KIT, kit, ignore=shutil.ignore_patterns(".git", "evals"))
        (kit / "platforms" / "ci" / "schemas" / "fake.schema.json").write_text('{"fake": 1}\n')
        script = kit / "platforms" / "tools" / "sync-project.sh"
        anchor = '  echo "$KIT_DIR/platforms/ci/validations/check_spec.py check_spec.py"\n'
        text = script.read_text()
        self.assertIn(anchor, text)
        script.write_text(text.replace(anchor, anchor + '  echo "$KIT_DIR/platforms/ci/schemas/fake.schema.json'
                                                        ' schemas/fake.schema.json"\n', 1))
        return script

    def run_kit(self, script, *args):
        env = dict(os.environ, AI_KIT_CLAUDE_PROBE="0")
        return subprocess.run(["bash", str(script), *args, str(self.repo)], capture_output=True, text=True,
                              check=False, env=env)

    def test_pin_records_every_kit_files_copy(self):  # coordinator request: a kit_files() entry added later is pinned
        script = self.kit_with_fake_spec_lint_file()
        result = self.run_kit(script, "--vendor-skills")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = json.loads((self.repo / ".claude" / "skills" / "KIT_MANIFEST.json").read_text())
        lint = self.repo / ".github" / "spec-lint"
        copies = {str(p.relative_to(self.repo)) for p in lint.rglob("*")
                  if p.is_file() and p.name not in ("README.md", "KIT_VERSION")}
        self.assertIn(".github/spec-lint/schemas/fake.schema.json", copies)
        self.assertEqual(set(manifest["copies"]), copies)
        fake = lint / "schemas" / "fake.schema.json"
        self.assertEqual(self.run_kit(script, "--check").returncode, 0)
        fake.write_text('{"fake": 2}\n')
        result = self.run_kit(script, "--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("sync: .github/spec-lint/schemas/fake.schema.json diverges from the pin", result.stdout)
        fake.unlink()
        result = self.run_kit(script, "--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("sync: .github/spec-lint/schemas/fake.schema.json is pinned but missing", result.stdout)

    def test_check_reports_a_kit_files_entry_the_pin_lacks(self):
        self.vendor_install()  # pinned by the kit as it is
        script = self.kit_with_fake_spec_lint_file()  # a later kit lists one more file
        result = self.run_kit(script, "--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("sync: .github/spec-lint/schemas/fake.schema.json is not in the pin (rerun sync-project.sh)",
                      result.stdout)

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
        self.assertIn("`.claude/skills/<skill>/`", client)
        self.assertIn("`~/.ai-kit/plugins/guardrails/skills/<skill>/`", client)

    def test_rule_copy_says_where_kit_skills_live(self):  # review of PR #261 (N4): Claude can open the references
        (self.repo / "client").mkdir()
        result = self.run_sync("--profile", "docs,godot:client")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        lines = self.text(".claude/rules/guardrails-code.md").splitlines()
        marker = next(i for i, line in enumerate(lines) if line.startswith("<!-- agent-rules-kit: generated from"))
        self.assertIn("`.claude/skills/<skill>/references/<file>`", lines[marker + 1])
        self.assertIn("`~/.ai-kit/plugins/guardrails/skills/<skill>/references/<file>`", lines[marker + 1])
        self.assertNotIn("`.claude/skills/<skill>/references/<file>`", self.text("client/AGENTS.md"))
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
