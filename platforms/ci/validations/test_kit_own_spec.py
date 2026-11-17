"""The kit runs its own FEAT-only flow (KIT-101): its .ai-kit.yaml is `project.kind: tooling` with `sdd.flow:
feat-only`, the `KIT` id prefix and `spec_root: docs/spec`; that spec validates with both validators, and the KIT
records written before the flow (docs/features/) stay outside spec_root, so no validator reads them."""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = (".ai-kit.yaml", "docs/spec/**", "platforms/ci/validations/check_spec.py",
          "platforms/ci/validations/spec_trace.py", "platforms/tools/profile.py")

KIT = Path(__file__).resolve().parents[3]
VALIDATIONS = KIT / "platforms" / "ci" / "validations"
SCHEMAS = KIT / "platforms" / "ci" / "schemas"


def run(*args, flags=()):
    env = {k: v for k, v in os.environ.items() if k != "CI"}
    return subprocess.run([sys.executable, "-B", *flags, *map(str, args)], capture_output=True, text=True,
                          check=False, env=env, cwd=KIT)


class KitOwnFlowTest(unittest.TestCase):
    def resolved(self):
        result = run(KIT / "platforms" / "tools" / "profile.py", "resolve", "--json", KIT)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr.strip(), "", "the kit's profile resolves with no note (check_kit.py § 15)")
        return json.loads(result.stdout)

    def spec_root(self):
        return KIT / self.resolved()["spec_root"]

    def test_the_profile_sets_the_tooling_flow(self):
        resolved = self.resolved()
        self.assertEqual(resolved["project"]["kind"], "tooling")
        self.assertEqual((resolved["sdd"]["flow"], resolved["sdd"]["id_prefix"]["feature"]), ("feat-only", "KIT"))
        self.assertEqual((resolved["sdd"]["needs"], resolved["sdd"]["task_table"]), (False, False))
        self.assertEqual(resolved["spec_root"], "docs/spec")

    def test_the_spec_validates_in_both_modes(self):
        spec = self.spec_root()
        self.assertTrue((spec / "spec.md").is_file(), spec)
        for flags in ((), ("-S",)):
            with self.subTest(flags=flags):
                result = run(VALIDATIONS / "check_spec.py", spec, SCHEMAS, flags=flags)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("spec: OK", result.stdout)

    def test_spec_trace_checks_it(self):
        result = run(VALIDATIONS / "spec_trace.py", "check", self.spec_root())
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_the_old_records_stay_outside_spec_root(self):
        spec = self.spec_root().resolve()
        old = sorted((KIT / "docs" / "features").glob("KIT-*.md"))
        self.assertGreater(len(old), 90)
        for path in old:
            self.assertNotIn(spec, path.resolve().parents, path)


if __name__ == "__main__":
    unittest.main()
