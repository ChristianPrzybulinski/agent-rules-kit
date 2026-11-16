"""The gitleaks workflow template (KIT-074): the pinned CLI, and its flags run against a throwaway repository with the
local gitleaks (redacted finding, .gitleaksignore, the config path input)."""
import json
import os
import re
import secrets
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("platforms/kits/github/workflows/gitleaks.yml",)

KIT = Path(__file__).resolve().parents[3]
TEMPLATE = KIT / "platforms" / "kits" / "github" / "workflows" / "gitleaks.yml"
GITLEAKS = shutil.which("gitleaks")


def pinned():
    text = TEMPLATE.read_text(encoding="utf-8")
    return re.search(r"GITLEAKS_VERSION: (\S+)", text).group(1), re.search(r"GITLEAKS_SHA256: (\S+)", text).group(1)


class Template(unittest.TestCase):
    LAYER = "contract"  # the kit's own files, read in-process

    def test_the_cli_is_pinned_by_version_and_sha256(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        version, digest = pinned()
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        self.assertRegex(digest, r"^[0-9a-f]{64}$")
        self.assertIn('sha256sum -c -', text)
        self.assertNotIn("uses: gitleaks/gitleaks-action", text)  # needs GITLEAKS_LICENSE in an organization's repo
        self.assertIn("fetch-depth: 0", text)

    def test_the_scan_redacts_and_takes_a_config_input(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("--redact", text)
        self.assertIn("--log-opts=HEAD", text)
        self.assertRegex(text, r"config:\n\s+description:")
        self.assertIn('args+=(--config "$CONFIG")', text)


@unittest.skipIf(GITLEAKS is None and not os.environ.get("CI"), "gitleaks is not on PATH (CI=1 makes it required)")
class Scan(unittest.TestCase):
    """The template's command line on a repository with a fabricated token (built at run time, never in this file)."""

    def setUp(self):
        if GITLEAKS is None:  # KIT-077: the CI jobs that run this layer install the pinned gitleaks
            self.fail("gitleaks is not on PATH")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.token = "ghp_" + secrets.token_hex(18)
        self.git("init", "-q")
        (self.repo / "app.env").write_text(f"GITHUB_TOKEN={self.token}\n", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "add config")

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=t", "-c", "user.email=t@t",
                        "-c", "commit.gpgsign=false", *args], check=True, capture_output=True)

    def scan(self, *extra):
        text = TEMPLATE.read_text(encoding="utf-8")
        args = re.search(r"args=\((.*)\)", text).group(1).split()
        report = self.repo.parent / f"{self.repo.name}-report.json"
        result = subprocess.run([GITLEAKS, *args, *extra, "--report-format", "json", "--report-path", str(report),
                                 "."], cwd=self.repo, capture_output=True, text=True)
        findings = json.loads(report.read_text(encoding="utf-8")) if report.exists() else []
        return result, findings

    def test_a_finding_fails_and_its_value_stays_out_of_the_log(self):
        result, findings = self.scan()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(len(findings), 1)
        self.assertNotIn(self.token, result.stdout + result.stderr)

    def test_gitleaksignore_holds_a_reviewed_fingerprint(self):
        _, findings = self.scan()
        (self.repo / ".gitleaksignore").write_text(findings[0]["Fingerprint"] + "\n", encoding="utf-8")
        result, findings = self.scan()
        self.assertEqual((result.returncode, findings), (0, []), result.stdout + result.stderr)

    def test_the_config_input_names_an_allowlist(self):
        (self.repo / "ci").mkdir()
        (self.repo / "ci" / "gitleaks.toml").write_text(
            '[extend]\nuseDefault = true\n\n[[allowlists]]\ndescription = "fixture"\npaths = [\'\'\'^app\\.env$\'\'\']\n',
            encoding="utf-8")
        result, findings = self.scan("--config", "ci/gitleaks.toml")
        self.assertEqual((result.returncode, findings), (0, []), result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
