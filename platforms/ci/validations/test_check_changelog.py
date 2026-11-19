"""check_changelog.py: a CHANGELOG line added under a released version fails (KIT-109), on throwaway repositories."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("platforms/tools/check_changelog.py",)

KIT = Path(__file__).resolve().parents[3]
SCRIPT = KIT / "platforms/tools/check_changelog.py"
GIT = ["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", "-c", "commit.gpgsign=false",
       "-c", "core.hooksPath=/dev/null", "-c", "maintenance.auto=false", "-c", "gc.auto=0"]

OLD = "# Changelog\n\n## [Unreleased]\n\n## [1.0.0] - 2026-01-01\n\n### Added\n- KIT-001: first.\n"
WITH_ENTRY = OLD.replace("## [Unreleased]\n", "## [Unreleased]\n\n### Added\n- KIT-002: second.\n", 1)
RELEASED = ("# Changelog\n\n## [Unreleased]\n\n## [1.1.0] - 2026-01-02\n\n### Added\n- KIT-002: second.\n\n"
            "## [1.0.0] - 2026-01-01\n\n### Added\n- KIT-001: first.\n")


def git(repo, *args):
    return subprocess.run([*GIT, "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout


class CheckChangelogTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        git(self.repo, "init", "-q", "-b", "main")

    def tearDown(self):
        self.tmp.cleanup()

    def commit(self, text, message="change"):
        (self.repo / "CHANGELOG.md").write_text(text, encoding="utf-8")
        git(self.repo, "add", "CHANGELOG.md")
        git(self.repo, "commit", "-q", "-m", message)

    def run_check(self, *extra):
        result = subprocess.run([sys.executable, str(SCRIPT), "--repo", str(self.repo), *extra],
                                capture_output=True, text=True, check=False)
        return result.returncode, result.stdout + result.stderr

    def test_a_line_under_unreleased_passes(self):
        self.commit(OLD, "base")
        self.commit(WITH_ENTRY)
        code, out = self.run_check()
        self.assertEqual(code, 0, out)
        self.assertIn("check_changelog: OK", out)

    def test_a_line_added_under_a_released_version_fails_and_names_it(self):
        self.commit(RELEASED, "base")
        self.commit(RELEASED.replace("- KIT-002: second.\n", "- KIT-002: second.\n- KIT-003: late.\n", 1))
        code, out = self.run_check()
        self.assertEqual(code, 1, out)
        self.assertIn("CHANGELOG.md:9: added under [1.1.0], a released version; move it under [Unreleased]", out)

    def test_a_release_diff_that_adds_the_heading_passes(self):
        """bump_version.py inserts the heading under [Unreleased]; the lines below it were not added."""
        self.commit(WITH_ENTRY, "base")
        self.commit(WITH_ENTRY.replace("## [Unreleased]\n", "## [Unreleased]\n\n## [1.1.0] - 2026-01-02\n", 1))
        code, out = self.run_check()
        self.assertEqual(code, 0, out)

    def test_a_release_diff_that_also_adds_lines_under_its_new_heading_passes(self):
        self.commit(OLD, "base")
        self.commit(RELEASED)
        code, out = self.run_check()
        self.assertEqual(code, 0, out)

    def test_a_rebase_across_a_release_lands_the_line_in_the_released_section(self):
        """The #386 story: the branch adds its line under [Unreleased]; main publishes 1.1.0 meanwhile."""
        self.commit(WITH_ENTRY.replace("- KIT-002: second.\n", "- KIT-002: second.\n\n### Fixed\n- KIT-004: x.\n"),
                    "base")
        git(self.repo, "branch", "feature")
        git(self.repo, "checkout", "-q", "feature")
        self.commit((self.repo / "CHANGELOG.md").read_text().replace(
            "### Fixed\n- KIT-004: x.\n", "### Fixed\n- KIT-004: x.\n- KIT-005: branch.\n"), "branch line")
        git(self.repo, "checkout", "-q", "main")
        self.commit((self.repo / "CHANGELOG.md").read_text().replace(
            "## [Unreleased]\n", "## [Unreleased]\n\n## [1.1.0] - 2026-01-02\n", 1), "release 1.1.0")
        git(self.repo, "checkout", "-q", "feature")
        git(self.repo, "update-ref", "refs/remotes/origin/main", "main")
        git(self.repo, "rebase", "-q", "main")
        code, out = self.run_check()
        self.assertEqual(code, 1, out)
        self.assertIn("added under [1.1.0]", out)

    def test_a_first_commit_has_no_base_and_passes(self):
        self.commit(OLD, "only")
        code, out = self.run_check()
        self.assertEqual(code, 0, out)
        self.assertIn("skipped", out)

    def test_an_explicit_base_is_used(self):
        self.commit(RELEASED, "base")
        base = git(self.repo, "rev-parse", "HEAD").strip()
        self.commit(RELEASED.replace("- KIT-001: first.\n", "- KIT-001: first.\n- KIT-009: late.\n", 1))
        self.commit(RELEASED.replace("- KIT-001: first.\n", "- KIT-001: first.\n- KIT-009: late.\n", 1).replace("late.", "later."), "edit")
        code, out = self.run_check("--base", base)
        self.assertEqual(code, 1, out)
        self.assertIn("added under [1.0.0]", out)


if __name__ == "__main__":
    unittest.main()
