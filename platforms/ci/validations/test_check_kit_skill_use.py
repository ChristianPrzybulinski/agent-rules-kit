"""check_kit.py on a throwaway copy (KIT-071): a subagent preloads only plugin-qualified, model-invocable kit skills,
and a `trigger` eval case repeats its AGENTS.md bullet in append_system_prompt.

A bare preload name resolved to Claude Code's bundled `review` instead of the kit skill (probe transcript, 2026-11-14),
and a skill with `disable-model-invocation: true` cannot be preloaded (Claude Code sub-agents doc)."""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LAYER = "integration"  # KIT-077 layer (platforms/tools/run_tests.py): starts processes (scripts, git, temp repos)
COVERS = ("platforms/ci/validations/check_kit.py", "plugins/guardrails/AGENTS.md", "plugins/guardrails/agents/**",
          "plugins/guardrails/evals/**")

KIT = Path(__file__).resolve().parents[3]
CHECK_KIT = "platforms/ci/validations/check_kit.py"
REVIEWER = "plugins/guardrails/agents/reviewer.md"
SDD_CHECK = "plugins/guardrails/skills/sdd-check/SKILL.md"
REVIEW_SKILL = "plugins/guardrails/skills/review/SKILL.md"
EVALS = "plugins/guardrails/evals"

try:
    import jsonschema  # noqa: F401
    import yaml  # noqa: F401
    FULL = True
except ImportError:
    FULL = False


class CheckKitSkillUseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.template = Path(cls.tmp.name) / "template"
        listed = subprocess.run(["git", "-C", str(KIT), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                                capture_output=True, text=True, check=True).stdout
        for rel in filter(None, listed.split("\0")):  # the working tree, so uncommitted edits count
            if (KIT / rel).is_file():
                (cls.template / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(KIT / rel, cls.template / rel)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.kit = Path(tempfile.mkdtemp(dir=self.tmp.name)) / "kit"
        shutil.copytree(self.template, self.kit)

    def check(self):
        return subprocess.run([sys.executable, "-B", str(self.kit / CHECK_KIT)], capture_output=True, text=True,
                              check=False)

    def preload(self, *names):
        path = self.kit / REVIEWER
        text = path.read_text(encoding="utf-8")
        block = "skills:\n" + "".join(f"  - {name}\n" for name in names)
        new = re.sub(r"skills:\n(?:  - .*\n)+", lambda _: block, text, count=1)
        self.assertNotEqual(new, text)
        path.write_text(new, encoding="utf-8")

    def trigger_case(self, name, frontmatter):
        """A synthetic eval case tagged trigger, so no wording of a real case or bullet is a precondition."""
        case = self.kit / EVALS / name
        (case / "graders").mkdir(parents=True)
        grader = "---\ntype: tool_used\ntool: Skill\n---\n"
        (case / "graders" / "skill-fired.md").write_text(grader, encoding="utf-8")
        (case / "prompt.md").write_text(f"---\ndescription: A fixture trigger case.\ntags: [trigger]\n{frontmatter}---\n\n"
                                        "Commit this change.\n", encoding="utf-8")
        return f"{EVALS}/{name}/prompt.md"

    def assert_fails(self, result, expected):
        """Each expected text in a FAIL line of its own and no other FAIL line: the mutations merged into one
        check_kit.py run neither mask nor add a failure."""
        lines = [line for line in result.stderr.splitlines() if line.startswith("FAIL: ")]
        self.assertNotEqual(result.returncode, 0)
        for text in expected:
            with self.subTest(text=text):
                self.assertEqual(sum(text in line for line in lines), 1, result.stderr)
        self.assertEqual([line for line in lines if not any(text in line for text in expected)], [], result.stderr)
        self.assertEqual(len(lines), len(expected), result.stderr)

    # The real kit passing is the static job's check_kit.py run (.github/workflows/ci.yml). Each preload is checked
    # on its own, so the wrong names go into one run, beside two valid ones that must add no line.

    def test_each_wrong_preload_fails(self):
        self.preload("review", "other:review", "guardrails:no-such-skill", "guardrails:sdd-implement",
                     "guardrails:security", "guardrails:review")
        self.assert_fails(self.check(), [
            "skills: 'review' needs its plugin prefix",
            "skills: 'other:review' is not a kit skill",
            "skills: 'guardrails:no-such-skill' is not a kit skill",
            "skills: 'guardrails:sdd-implement' is user-only; cannot be preloaded",
            # the bare name fails the profile schema's plugin:skill pattern too, where jsonschema is installed
            *(["schema agent.schema.json: 'review' does not match"] if FULL else []),
        ])

    def set_agent(self, value):
        path = self.kit / REVIEW_SKILL
        text = path.read_text(encoding="utf-8")
        new = re.sub(r"^agent: .*$", f"agent: {value}", text, count=1, flags=re.MULTILINE)
        self.assertNotEqual(new, text)
        path.write_text(new, encoding="utf-8")

    # KIT-114: a plugin agent resolves in a skill's `agent:` only as <plugin>:<profile> (probe, Claude Code 2.1.287:
    # `researcher` ran as general-purpose on the parent's model, `guardrails:researcher` as the profile).

    def test_the_real_kit_names_its_agents_with_their_plugin(self):
        review = (self.kit / REVIEW_SKILL).read_text(encoding="utf-8")
        self.assertRegex(review, r"(?m)^agent: guardrails:reviewer$")
        # sdd-check stays a general-purpose fork: the NEED-010 replay (2026-11-19) showed the researcher profile
        # (sonnet, no Bash) missed the critical and high findings Opus reported, so it must not declare an agent
        sdd_check = (self.kit / SDD_CHECK).read_text(encoding="utf-8")
        self.assertRegex(sdd_check, r"(?m)^subagent: true$")
        self.assertNotRegex(sdd_check, r"(?m)^agent:")
        self.assertEqual(self.check().returncode, 0)

    def test_another_qualified_agent_passes(self):
        self.set_agent("guardrails:researcher")
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_each_wrong_agent_name_fails(self):
        for value, expected in (
            ("researcher", "agent 'researcher' needs its plugin prefix (guardrails:researcher)"),
            ("other:researcher", "agent 'other:researcher' has no agents/ profile in plugin 'other'"),
            ("guardrails:no-such-agent", "agent 'guardrails:no-such-agent' has no agents/ profile in plugin 'guardrails'"),
            ("no-such-agent", "agent 'no-such-agent' has no agents/ profile in any plugin"),
        ):
            with self.subTest(agent=value):
                self.set_agent(value)
                self.assert_fails(self.check(), [expected])

    @unittest.skipUnless(FULL, "needs pyyaml to read the eval frontmatter")
    def test_a_trigger_case_without_its_bullet_fails(self):
        missing = self.trigger_case("fixture-trigger-without-append", "")
        drifted = self.trigger_case("fixture-trigger-drifted-append",
                                    'append_system_prompt: "A line that repeats no bullet of AGENTS.md."\n')
        self.assert_fails(self.check(), [
            f"{missing}: a trigger case needs append_system_prompt",
            f"{drifted}: append_system_prompt must repeat one bullet",
        ])


if __name__ == "__main__":
    unittest.main()
