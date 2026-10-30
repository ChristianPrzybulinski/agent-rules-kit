"""bump_version.py: release bump and --notes on a throwaway copy of the kit (KIT-019)."""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[3]
SCRIPT = "platforms/tools/bump_version.py"
CHECK_KIT = "platforms/ci/validations/check_kit.py"
GIT = ["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid",
       "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
       "-c", "maintenance.auto=false", "-c", "gc.auto=0"]  # a background repack races the clone
ENTRY = "- KIT-000: a test entry."
DAY = "2026-01-02"


def git(repo, *args):
    return subprocess.run([*GIT, "-C", str(repo), *args], capture_output=True, text=True,
                          check=True).stdout


def release_awk():
    """The CHANGELOG extraction command of release.yml, without its redirection."""
    for line in (KIT / ".github/workflows/release.yml").read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("awk -v t="):
            return line.strip().split(" > notes.md")[0]
    raise AssertionError("release.yml has no awk extraction")


class BumpVersionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.template = Path(cls.tmp.name) / "template"
        listed = git(KIT, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
        for rel in filter(None, listed.split("\0")):  # the working tree, so uncommitted edits count
            if (KIT / rel).is_file():
                (cls.template / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(KIT / rel, cls.template / rel)
        git(cls.template, "init", "-q")
        git(cls.template, "add", "-A")
        git(cls.template, "commit", "-q", "-m", "copy")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.repo = Path(tempfile.mkdtemp(dir=self.tmp.name)) / "kit"
        git(self.tmp.name, "clone", "-q", str(self.template), str(self.repo))
        self.current = (self.repo / "VERSION").read_text(encoding="utf-8").strip()
        major, minor, _ = (int(part) for part in self.current.split("."))
        self.next_minor = f"{major}.{minor + 1}.0"

    def run_bump(self, *args):
        return subprocess.run([sys.executable, str(self.repo / SCRIPT), *args],
                              capture_output=True, text=True, check=False)

    def set_unreleased(self, body):
        path = self.repo / "CHANGELOG.md"
        text = re.sub(r"(?ms)^(## \[Unreleased\]\n).*?(?=^## \[)", lambda m: m.group(1) + body,
                      path.read_text(encoding="utf-8"), count=1)
        path.write_text(text, encoding="utf-8")
        git(self.repo, "commit", "-q", "-am", "unreleased")

    def assert_untouched(self, result, reason):
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(reason, result.stderr)
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")

    def test_bump_keeps_check_kit_green(self):
        self.set_unreleased(f"\n### Added\n{ENTRY}\n\n")
        old_field = f'"version": "{self.current}"'
        manifests = git(self.repo, "grep", "-c", "-F", old_field, "--",
                        "*plugin.json", "*marketplace.json").split()
        fields = sum(int(line.rsplit(":", 1)[1]) for line in manifests)
        result = self.run_bump(self.next_minor, "--date", DAY)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f"bump: {fields} version fields in {len(manifests)} manifests", result.stdout)
        changed = set(git(self.repo, "diff", "--name-only").split())
        self.assertEqual(changed, {"VERSION", "CHANGELOG.md"}
                         | {line.rsplit(":", 1)[0] for line in manifests})
        self.assertEqual((self.repo / "VERSION").read_text(encoding="utf-8"), self.next_minor + "\n")
        self.assertIn(f"## [Unreleased]\n\n## [{self.next_minor}] - {DAY}\n\n### Added\n{ENTRY}\n",
                      (self.repo / "CHANGELOG.md").read_text(encoding="utf-8"))
        check = subprocess.run([sys.executable, "-B", CHECK_KIT], cwd=self.repo,
                               capture_output=True, text=True, check=False)
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        self.assertEqual(self.run_bump("--notes", self.next_minor).stdout,
                         self.awk_notes(self.next_minor))

    def test_refuses_equal_lower_or_non_semver_version(self):
        self.set_unreleased(f"\n{ENTRY}\n\n")
        for value in (self.current, "0.0.0"):
            self.assert_untouched(self.run_bump(value), "is not greater than VERSION")
        for value in ("12.0", "v12.0.0", "012.0.0", "12.0.0-rc.1"):
            self.assert_untouched(self.run_bump(value), "is not SemVer")

    def test_refuses_empty_unreleased(self):
        self.set_unreleased("\n### Added\n\n")
        self.assert_untouched(self.run_bump(self.next_minor), "has no entry")

    def test_refuses_dirty_tree(self):
        self.set_unreleased(f"\n{ENTRY}\n\n")
        (self.repo / "scratch.txt").write_text("x\n", encoding="utf-8")
        result = self.run_bump(self.next_minor)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("the working tree is not clean", result.stderr)
        self.assertEqual(git(self.repo, "status", "--porcelain"), "?? scratch.txt\n")

    def awk_notes(self, version):
        result = subprocess.run(["bash", "-c", release_awk()], cwd=self.repo,
                                env={"PATH": "/usr/bin:/bin", "GITHUB_REF_NAME": f"v{version}"},
                                capture_output=True, text=True, check=True)
        return result.stdout

    def test_notes_match_release_yml_extraction(self):
        changelog = (self.repo / "CHANGELOG.md").read_text(encoding="utf-8")
        versions = re.findall(r"(?m)^## \[(\d+\.\d+\.\d+)\]", changelog)
        self.assertIn(self.current, versions)
        for version in versions:
            result = self.run_bump("--notes", version)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(result.stdout.startswith(f"## [{version}]"), version)
            self.assertEqual(result.stdout, self.awk_notes(version), version)
        missing = self.run_bump("--notes", "0.0.0")
        self.assertEqual(missing.returncode, 1)
        self.assertIn("section ## [0.0.0] not found", missing.stderr)


if __name__ == "__main__":
    unittest.main()
