"""smoke.sh (KIT-077): its main path, bootstrap into an empty home, the Codex AGENTS.md link and its repoints, then a
clean doctor run, is one integration test a pull request runs when it touches those parts; the whole script, every
lifecycle case after the main path, belongs to the functional layer (ci-full: push to main, nightly, release)."""
import os
import subprocess
import unittest
from pathlib import Path

LAYER = "integration"
KIT = Path(__file__).resolve().parents[3]
SMOKE = KIT / "platforms" / "tools" / "smoke.sh"


def run_smoke(*args, timeout):
    return subprocess.run(["bash", str(SMOKE), *args], capture_output=True, text=True, errors="replace",
                          env=dict(os.environ), timeout=timeout, check=False)


class SmokeMainPath(unittest.TestCase):
    COVERS = ("platforms/tools/smoke.sh", "platforms/tools/bootstrap.sh", "platforms/tools/doctor.sh",
              "platforms/tools/refresh.sh", "platforms/ci/validations/check_kit.py", "platforms/kits/launchd/**",
              ".claude-plugin/**", ".agents/**", "plugins/*/.claude-plugin/**",
              "plugins/*/.devin-plugin/**", "plugins/*/plugin.json", "plugins/guardrails/AGENTS.md")

    def test_bootstrap_and_doctor_pass_in_an_empty_home(self):
        result = run_smoke("--main", timeout=300)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("smoke: main path OK", result.stdout)

    def test_an_unknown_argument_is_a_usage_error(self):
        result = run_smoke("--all", timeout=30)
        self.assertEqual((result.returncode, result.stderr), (2, "usage: smoke.sh [--main]\n"))


class SmokeWhole(unittest.TestCase):
    LAYER = "functional"

    def test_every_lifecycle_case_passes(self):
        result = run_smoke(timeout=900)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("smoke: OK (", result.stdout)


if __name__ == "__main__":
    unittest.main()
