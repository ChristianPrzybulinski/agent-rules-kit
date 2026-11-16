"""KIT-081 stage 2a: every install of the kit follows its `stable` branch, which release.yml moves to each release.
kit-release.sh names the branch and reads the ref of Claude Code's ai-kit marketplace; bootstrap.sh adds Claude Code's
and Codex's marketplaces at `stable`; refresh.sh moves each one to `stable` once (Claude Code's plugin data copied to a
dated backup before the remove and restored after the install) and then only updates it; doctor.sh fails while Claude
Code's or Codex's marketplace, or Devin's plugin, follows another ref. Stub claude and codex CLIs keep their state in a
throwaway home, and every script runs with a fresh environment: nothing here reads or writes the real home."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)

KIT = Path(__file__).resolve().parents[3]
TOOLS = KIT / "platforms" / "tools"
REPOSITORY = "ChristianPrzybulinski/agent-rules-kit"
RESTRICTED_PATH = "/usr/bin:/bin"
GIT = ("-c", "maintenance.auto=false", "-c", "gc.auto=0", "-c", "user.name=test", "-c", "user.email=t@example.invalid")

# Claude Code 2.1.287 as measured in a throwaway home (KIT-081): the marketplace's source, ref included, sits in
# <plugins root>/known_marketplaces.json; `marketplace remove` uninstalls the marketplace's plugins and deletes their
# data folders <plugins root>/data/<plugin>-<marketplace>/; a second add is refused while the first source is declared.
# $STUB_FAIL names the step that fails; $STUB_INSTALL_WRITES makes an install write plugin data, as a session's hook
# could right after it.
CLAUDE_STUB = r'''#!/usr/bin/env python3
import json, os, shutil, sys
from pathlib import Path

args = sys.argv[1:]
cmd = " ".join(args)
state = Path(os.environ["STUB_STATE"])
with open(str(state / "calls.log"), "a") as log:
    log.write("claude " + cmd + "\n")
config = Path(os.environ.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude"))
root = Path(os.environ.get("CLAUDE_CODE_PLUGIN_CACHE_DIR") or str(config / "plugins"))
known_path = root / "known_marketplaces.json"
known = json.loads(known_path.read_text()) if known_path.is_file() else {}
installed_path = state / "claude-installed.json"
installed = json.loads(installed_path.read_text()) if installed_path.is_file() else []


def save():
    root.mkdir(parents=True, exist_ok=True)
    known_path.write_text(json.dumps(known))
    installed_path.write_text(json.dumps(installed))


def step(name):
    if os.environ.get("STUB_FAIL") == name:
        print("stub claude: " + name + " failed", file=sys.stderr)
        sys.exit(1)


if cmd == "plugin marketplace list --json":
    print(json.dumps([dict(name=name, **entry["source"]) for name, entry in known.items()]))
elif args[:3] == ["plugin", "marketplace", "add"]:
    step("add")
    if "ai-kit" in known:
        print("stub claude: marketplace ai-kit is already declared", file=sys.stderr)
        sys.exit(1)
    repo, _, ref = args[3].partition("#")
    source = {"source": "github", "repo": repo}
    if ref:
        source["ref"] = ref
    known["ai-kit"] = {"source": source, "installLocation": str(root / "marketplaces" / "ai-kit")}
    save()
    print('{"outcome":"ok"}')
elif args[:4] == ["plugin", "marketplace", "remove", "ai-kit"]:
    step("remove")
    known.pop("ai-kit", None)
    for plugin in [p for p in installed if p.endswith("@ai-kit")]:
        shutil.rmtree(str(root / "data" / plugin.replace("@", "-")), ignore_errors=True)
    installed[:] = [p for p in installed if not p.endswith("@ai-kit")]
    save()
    print('{"outcome":"ok"}')
elif cmd == "plugin list --json":
    print(json.dumps([{"id": plugin, "scope": "user"} for plugin in installed]))
elif args[:2] == ["plugin", "install"]:
    step("install")
    if "ai-kit" not in known:
        print("stub claude: no marketplace ai-kit", file=sys.stderr)
        sys.exit(1)
    if args[2] not in installed:
        installed.append(args[2])
    save()
    if os.environ.get("STUB_INSTALL_WRITES"):
        data = root / "data" / args[2].replace("@", "-")
        data.mkdir(parents=True, exist_ok=True)
        with open(str(data / "instructions-loaded.jsonl"), "a") as handle:
            handle.write('{"after": 1}\n')
        (data / "settings.json").write_text("new\n")
    print('{"outcome":"ok"}')
elif cmd == "plugin marketplace update ai-kit --json" or args[:2] in (["plugin", "update"], ["plugin", "uninstall"]):
    print('{"outcome":"ok"}')
else:
    print("unexpected claude stub arguments: " + cmd, file=sys.stderr)
    sys.exit(2)
'''

# Codex keeps the ai-kit marketplace and its ref in config.toml ([marketplaces.ai-kit]), as codex-cli 0.164.0 does.
CODEX_STUB = r'''#!/usr/bin/env python3
import os, sys
from pathlib import Path

args = sys.argv[1:]
cmd = " ".join(args)
state = Path(os.environ["STUB_STATE"])
with open(str(state / "calls.log"), "a") as log:
    log.write("codex " + cmd + "\n")
config = Path(os.environ.get("CODEX_HOME") or str(Path.home() / ".codex")) / "config.toml"
text = config.read_text() if config.is_file() else ""


def without_marketplace():
    kept, skipping = [], False
    for line in text.splitlines():
        if line.startswith("["):
            skipping = line.strip() == "[marketplaces.ai-kit]"
        if not skipping:
            kept.append(line)
    return "\n".join(kept) + "\n" if kept else ""


if cmd == "plugin marketplace list":
    if "[marketplaces.ai-kit]" in text:
        print("ai-kit ChristianPrzybulinski/agent-rules-kit")
elif args[:3] == ["plugin", "marketplace", "add"]:
    ref = args[args.index("--ref") + 1]
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(without_marketplace() + '[marketplaces.ai-kit]\nsource_type = "git"\nref = "' + ref + '"\n')
elif cmd == "plugin marketplace remove ai-kit":
    config.write_text(without_marketplace())
elif cmd == "plugin list":
    print("guardrails@ai-kit  installed, enabled")
elif cmd == "debug prompt-input list skills":
    print("guardrails:review")
elif cmd == "plugin marketplace upgrade ai-kit" or args[:2] in (["plugin", "add"], ["plugin", "remove"]):
    pass
else:
    print("unexpected codex stub arguments: " + cmd, file=sys.stderr)
    sys.exit(2)
'''


def git(*args, cwd):
    subprocess.run(["git", *GIT, *args], cwd=cwd, check=True, capture_output=True, text=True)


class StableHome(unittest.TestCase):
    """A kit origin with one release tag, a throwaway home with its clone, and the stub CLIs first on PATH."""

    @classmethod
    def setUpClass(cls):
        cls.origin_dir = tempfile.TemporaryDirectory()
        origin = Path(cls.origin_dir.name) / "origin"
        plugin = origin / "plugins" / "guardrails"
        for marker in (".claude-plugin", ".devin-plugin"):
            (plugin / marker).mkdir(parents=True)
            (plugin / marker / "plugin.json").write_text('{"name": "guardrails"}\n')
        (plugin / "plugin.json").write_text('{"name": "guardrails"}\n')
        (plugin / "AGENTS.md").write_text("# Global Rules — AI Kit\n")
        (origin / "platforms" / "tools").mkdir(parents=True)
        for name in ("bootstrap.sh", "refresh.sh", "doctor.sh", "codex-bin.sh", "kit-release.sh"):
            shutil.copy2(TOOLS / name, origin / "platforms" / "tools" / name)
        git("init", "-q", "-b", "main", cwd=origin)
        git("add", "-A", cwd=origin)
        git("commit", "-qm", "fixture", cwd=origin)
        git("tag", "v0.0.0", cwd=origin)
        cls.origin = origin

    @classmethod
    def tearDownClass(cls):
        cls.origin_dir.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"
        self.state = self.root / "stub-state"
        self.bin = self.root / "bin"
        for folder in (self.home, self.state, self.bin):
            folder.mkdir()
        for name, text in (("claude", CLAUDE_STUB), ("codex", CODEX_STUB)):
            (self.bin / name).write_text(text)
            (self.bin / name).chmod(0o755)
        self.kit = self.home / ".ai-kit"
        self.plugins_root = self.home / ".claude" / "plugins"
        self.data = self.plugins_root / "data" / "guardrails-ai-kit"
        self.backups = self.home / "state" / "ai-kit" / "plugin-data-backup"

    def tearDown(self):
        self.tmp.cleanup()

    def clone(self):
        subprocess.run(["git", "clone", "-q", str(self.origin), str(self.kit)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.kit), "checkout", "-q", "--detach", "v0.0.0"], check=True,
                       capture_output=True)

    def env(self, **extra):
        env = {"HOME": str(self.home), "PATH": f"{self.bin}:{RESTRICTED_PATH}", "AI_KIT_DIR": str(self.kit),
               "STUB_STATE": str(self.state), "AI_KIT_NO_CODEX_CLI": "0", "AI_KIT_SESSION_AUDIT": "0",
               "AI_KIT_NO_LAUNCHD": "1", "XDG_STATE_HOME": str(self.home / "state"), "LANG": "C.UTF-8"}
        env.update(extra)
        return env

    def run_tool(self, name, **extra):
        return subprocess.run(["bash", str(TOOLS / name)], capture_output=True, text=True, errors="replace",
                              env=self.env(**extra), timeout=180, check=False)

    def calls(self):
        log = self.state / "calls.log"
        return log.read_text().splitlines() if log.is_file() else []

    def set_claude(self, ref=None, installed=True):
        """Claude Code's ai-kit marketplace at `ref` (None: declared without one, so it follows main)."""
        source = {"source": "github", "repo": REPOSITORY}
        if ref:
            source["ref"] = ref
        self.plugins_root.mkdir(parents=True, exist_ok=True)
        (self.plugins_root / "known_marketplaces.json").write_text(json.dumps({"ai-kit": {"source": source}}))
        (self.state / "claude-installed.json").write_text(json.dumps(["guardrails@ai-kit"] if installed else []))

    def claude_ref(self):
        known = json.loads((self.plugins_root / "known_marketplaces.json").read_text())
        return known["ai-kit"]["source"].get("ref")

    def set_codex(self, ref):
        (self.home / ".codex").mkdir(parents=True, exist_ok=True)
        (self.home / ".codex" / "config.toml").write_text(
            f'[marketplaces.ai-kit]\nsource_type = "git"\nref = "{ref}"\n')

    def codex_ref(self):
        text = (self.home / ".codex" / "config.toml").read_text()
        return next(line.split('"')[1] for line in text.splitlines() if line.startswith("ref = "))

    def write_data(self):
        """The plugin data a session left: the rule-load log, a settings file and a nested note."""
        (self.data / "notes").mkdir(parents=True)
        (self.data / "instructions-loaded.jsonl").write_text('{"before": 1}\n{"before": 2}\n')
        (self.data / "settings.json").write_text("old\n")
        (self.data / "notes" / "x.txt").write_text("kept\n")


class ClaudeKitRef(StableHome):
    """kit-release.sh: the branch name, and the ref of Claude Code's ai-kit marketplace, `<absent>` when it has none."""
    COVERS = ("platforms/tools/kit-release.sh",)

    def helper(self, expression, **extra):
        script = f'source "{TOOLS / "kit-release.sh"}"; {expression}'
        result = subprocess.run(["bash", "-c", script], capture_output=True, text=True, env=self.env(**extra),
                                timeout=30, check=False)
        return result.stdout.strip() + result.stderr.strip()

    def test_the_branch_every_install_follows_is_stable(self):
        self.assertEqual(self.helper('printf "%s" "$KIT_STABLE_BRANCH"'), "stable")

    def test_reads_the_ref_from_known_marketplaces(self):
        self.set_claude("stable")
        self.assertEqual(self.helper("claude_kit_ref"), "stable")
        self.set_claude("v13.1.0")
        self.assertEqual(self.helper("claude_kit_ref"), "v13.1.0")

    def test_absent_without_a_ref(self):
        self.assertEqual(self.helper("claude_kit_ref"), "<absent>")  # no file
        self.set_claude(None)
        self.assertEqual(self.helper("claude_kit_ref"), "<absent>")  # declared without a ref: Claude follows main
        (self.plugins_root / "known_marketplaces.json").write_text('{"other": {"source": {"ref": "stable"}}}')
        self.assertEqual(self.helper("claude_kit_ref"), "<absent>")
        (self.plugins_root / "known_marketplaces.json").write_text("{not json")
        self.assertEqual(self.helper("claude_kit_ref"), "<absent>")

    def test_honours_the_claude_config_and_plugin_folders(self):
        self.set_claude("main")
        config = self.root / "config"
        (config / "plugins").mkdir(parents=True)
        (config / "plugins" / "known_marketplaces.json").write_text(
            json.dumps({"ai-kit": {"source": {"repo": REPOSITORY, "ref": "stable"}}}))
        self.assertEqual(self.helper("claude_kit_ref", CLAUDE_CONFIG_DIR=str(config)), "stable")
        cache = self.root / "cache"
        cache.mkdir()
        (cache / "known_marketplaces.json").write_text(json.dumps({"ai-kit": {"source": {"ref": "v1.0.0"}}}))
        self.assertEqual(self.helper("claude_kit_ref", CLAUDE_CONFIG_DIR=str(config),
                                     CLAUDE_CODE_PLUGIN_CACHE_DIR=str(cache)), "v1.0.0")


class Bootstrap(StableHome):
    COVERS = ("platforms/tools/bootstrap.sh", "platforms/tools/kit-release.sh")

    def test_adds_both_marketplaces_at_stable(self):
        result = self.run_tool("bootstrap.sh", AI_KIT_SOURCE=str(self.origin))
        calls = self.calls()
        self.assertIn(f"claude plugin marketplace add {REPOSITORY}#stable --json", calls, result.stdout + result.stderr)
        self.assertIn(f"codex plugin marketplace add {REPOSITORY} --ref stable", calls, result.stdout + result.stderr)
        self.assertIn("fix: kit clone at release v0.0.0", result.stdout)
        self.assertEqual((self.claude_ref(), self.codex_ref()), ("stable", "stable"))


class RefreshMovesToStable(StableHome):
    """refresh.sh moves each marketplace to `stable` once; from then on it only updates."""
    COVERS = ("platforms/tools/refresh.sh", "platforms/tools/kit-release.sh", "platforms/tools/codex-bin.sh")

    def setUp(self):
        super().setUp()
        self.clone()

    def refresh(self, **extra):
        before = len(self.calls())
        result = self.run_tool("refresh.sh", **extra)
        return result, self.calls()[before:]

    def backup_folders(self):
        return sorted(self.backups.iterdir()) if self.backups.is_dir() else []

    def test_claude_moves_once_and_keeps_its_plugin_data(self):
        self.set_claude(None)
        self.set_codex("stable")
        self.write_data()
        result, calls = self.refresh(STUB_INSTALL_WRITES="1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        claude = [call for call in calls if call.startswith("claude plugin marketplace remove")
                  or call.startswith("claude plugin marketplace add") or call.startswith("claude plugin install")]
        self.assertEqual(claude, ["claude plugin marketplace remove ai-kit --scope user --json",
                                  f"claude plugin marketplace add {REPOSITORY}#stable --json",
                                  "claude plugin install guardrails@ai-kit --scope user --json"])
        self.assertEqual(self.claude_ref(), "stable")
        self.assertIn("refresh: claude marketplace ai-kit moved from <absent> to stable", result.stdout)
        [backup] = self.backup_folders()
        self.assertRegex(backup.name, r"^\d{8}T\d{6}Z$")
        self.assertEqual((backup / "guardrails-ai-kit" / "instructions-loaded.jsonl").read_text(),
                         '{"before": 1}\n{"before": 2}\n')
        self.assertIn(f"refresh: claude: backed up {self.data} to {backup / 'guardrails-ai-kit'}", result.stdout)
        # The rule-load log keeps the backup's lines first, then the line written after the reinstall; a file the
        # reinstall wrote is newer and stays; a file only the backup holds comes back.
        self.assertEqual((self.data / "instructions-loaded.jsonl").read_text(),
                         '{"before": 1}\n{"before": 2}\n{"after": 1}\n')
        self.assertEqual((self.data / "settings.json").read_text(), "new\n")
        self.assertEqual((self.data / "notes" / "x.txt").read_text(), "kept\n")

        result, calls = self.refresh(STUB_INSTALL_WRITES="1")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse([call for call in calls if "marketplace remove" in call or "marketplace add" in call], calls)
        self.assertIn("claude plugin marketplace update ai-kit --json", calls)
        self.assertIn("claude plugin update guardrails@ai-kit --json", calls)
        self.assertEqual(len(self.backup_folders()), 1)
        self.assertEqual((self.data / "instructions-loaded.jsonl").read_text(),
                         '{"before": 1}\n{"before": 2}\n{"after": 1}\n')

    def test_claude_data_comes_back_whole_into_an_empty_folder(self):
        self.set_claude("v0.0.0")
        self.set_codex("stable")
        self.write_data()
        result, _ = self.refresh()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("refresh: claude marketplace ai-kit moved from v0.0.0 to stable", result.stdout)
        self.assertEqual((self.data / "instructions-loaded.jsonl").read_text(), '{"before": 1}\n{"before": 2}\n')
        self.assertEqual((self.data / "settings.json").read_text(), "old\n")
        self.assertEqual((self.data / "notes" / "x.txt").read_text(), "kept\n")

    def test_a_failed_move_names_the_commands_left_and_keeps_the_backup(self):
        self.set_claude(None)
        self.set_codex("stable")
        self.write_data()
        result, _ = self.refresh(STUB_FAIL="add")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        [backup] = self.backup_folders()
        self.assertIn(f"claude plugin marketplace add {REPOSITORY}#stable && "
                      "claude plugin install guardrails@ai-kit --scope user", result.stderr)
        self.assertIn(str(backup), result.stderr)
        self.assertEqual((backup / "guardrails-ai-kit" / "instructions-loaded.jsonl").read_text(),
                         '{"before": 1}\n{"before": 2}\n')

    def test_codex_moves_once_then_upgrades(self):
        self.set_claude("stable")
        self.set_codex("v0.0.0")
        result, calls = self.refresh()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        codex = [call for call in calls if call.startswith("codex plugin marketplace") or call.startswith("codex plugin add")]
        self.assertEqual(codex, ["codex plugin marketplace list", "codex plugin marketplace remove ai-kit",
                                 f"codex plugin marketplace add {REPOSITORY} --ref stable",
                                 "codex plugin add guardrails@ai-kit"])
        self.assertIn("refresh: codex marketplace ai-kit moved from v0.0.0 to stable", result.stdout)
        self.assertEqual(self.codex_ref(), "stable")
        result, calls = self.refresh()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual([call for call in calls if call.startswith("codex plugin marketplace")],
                         ["codex plugin marketplace list", "codex plugin marketplace upgrade ai-kit"])
        self.assertEqual(self.backup_folders(), [])  # Claude was on stable: nothing moved, nothing backed up


class DoctorWantsStable(StableHome):
    """doctor.sh fails while a marketplace or Devin's plugin follows another ref; it moves Codex itself, never Claude
    Code, whose move deletes the plugin data that refresh.sh backs up first."""
    COVERS = ("platforms/tools/doctor.sh", "platforms/tools/kit-release.sh", "platforms/tools/codex-bin.sh")

    def setUp(self):
        super().setUp()
        self.clone()

    def doctor(self):
        result = self.run_tool("doctor.sh")
        return result, [line for line in result.stderr.splitlines() if line.startswith("FAIL:")]

    def set_devin(self, ref):
        sha = subprocess.run(["git", "-C", str(self.kit), "rev-parse", "v0.0.0^{commit}"], capture_output=True,
                             text=True, check=True).stdout.strip()
        lock = self.home / ".local" / "share" / "devin" / "cli" / "plugins" / "lock.json"
        lock.parent.mkdir(parents=True)
        lock.write_text(json.dumps({"resolved": [{"name": "guardrails", "spec": {"ref": ref},
                                                  "resolved": {"sha": sha}}]}))

    def ref_failures(self, failures):
        return [line for line in failures if "marketplace" in line or "devin" in line]

    def test_every_install_on_stable_passes(self):
        self.set_claude("stable")
        self.set_codex("stable")
        self.set_devin("stable")
        result, failures = self.doctor()
        self.assertEqual(self.ref_failures(failures), [], result.stdout + result.stderr)
        for line in ("ok: claude marketplace ai-kit registered at stable",
                     "ok: codex marketplace ai-kit registered at stable",
                     "ok: devin plugin follows stable at release v0.0.0"):
            self.assertIn(line, result.stdout)

    def test_claude_off_stable_fails_with_the_refresh_command(self):
        self.set_claude(None)
        self.set_codex("stable")
        result, failures = self.doctor()
        self.assertIn(f"FAIL: claude marketplace ai-kit follows <absent>, not stable — run: bash "
                      f"{self.kit}/platforms/tools/refresh.sh", failures, result.stdout + result.stderr)
        self.assertFalse([call for call in self.calls() if call.startswith("claude plugin marketplace remove")])
        self.assertIsNone(self.claude_ref())

    def test_codex_off_stable_is_moved(self):
        self.set_claude("stable")
        self.set_codex("v0.0.0")
        result, failures = self.doctor()
        self.assertEqual(self.ref_failures(failures), [], result.stdout + result.stderr)
        self.assertIn("fix: codex marketplace ai-kit moved from v0.0.0 to stable", result.stdout)
        self.assertIn("fix: codex plugin guardrails@ai-kit installed", result.stdout)
        self.assertEqual(self.codex_ref(), "stable")

    def test_devin_off_stable_fails_with_where_to_set_it(self):
        self.set_claude("stable")
        self.set_codex("stable")
        self.set_devin("v0.0.0")
        result, failures = self.doctor()
        self.assertIn("FAIL: devin plugin ref is 'v0.0.0', not stable — set stable in Customize → Plugins → "
                      "Plugin settings → Edit manifest", failures, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
