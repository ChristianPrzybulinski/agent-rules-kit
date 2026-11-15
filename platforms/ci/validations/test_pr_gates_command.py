"""pr_gates.command_allowed (KIT-073): the one proof-command predicate the PR gates, review_checks.py and
row_checks.py share — allowlist, refused constructs, the `! git diff` trap and the optional working-directory sandbox."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from pr_gates import command_allowed  # noqa: E402

ALLOW = ["python3", "grep", "git", "test", "godot", "./mvnw", "!"]
DEPTHS = {"PROTOCOL_DIR": 1, "HOME": 1, "TMPDIR": 1, "JAVA_HOME": 0}


class Allowlist(unittest.TestCase):
    def test_allowlisted_chains_pass_and_others_fail(self):
        self.assertTrue(command_allowed("./mvnw -q verify && grep -q x a.txt", ALLOW)[0])
        self.assertEqual(command_allowed("docker ps", ALLOW), (False, "'docker' not in allowlist"))
        self.assertEqual(command_allowed("grep x a & curl y", ALLOW), (False, "forbidden construct"))
        self.assertEqual(command_allowed("grep x a & ls", ALLOW), (False, "'ls' not in allowlist"))

    def test_refused_constructs_and_redirections(self):
        for cmd in ("echo $(id)", "grep `id` a", "rm -rf x", "ssh host"):
            self.assertEqual(command_allowed(cmd, ALLOW), (False, "forbidden construct"), cmd)
        self.assertEqual(command_allowed("grep x a > out.txt", ALLOW)[1], "redirection other than to /dev/null")
        self.assertTrue(command_allowed("grep x a > /dev/null 2>&1", ALLOW)[0])
        self.assertTrue(command_allowed('grep -q "<tag> a|b" file.xml', ALLOW)[0])

    def test_negated_git_diff_needs_quiet_or_exit_code(self):
        ok, why = command_allowed("! git diff --name-only HEAD~1", ALLOW)
        self.assertFalse(ok)
        self.assertIn("--quiet", why)
        self.assertTrue(command_allowed("! git diff --quiet HEAD~1 -- a", ALLOW)[0])
        self.assertTrue(command_allowed("! git diff --exit-code HEAD~1", ALLOW)[0])
        self.assertTrue(command_allowed("git diff --name-only HEAD~1", ALLOW)[0])

    def test_two_arguments_keep_the_previous_behaviour(self):
        self.assertTrue(command_allowed("python3 ../tools/x.py", ALLOW)[0])
        self.assertTrue(command_allowed("test -f /etc/hosts", ALLOW)[0])


class Sandbox(unittest.TestCase):
    def test_a_component_may_not_read_outside_its_folder(self):
        ok, why = command_allowed("python3 ../tools/x.py", ALLOW, cwd="server")
        self.assertFalse(ok)
        self.assertIn("../tools/x.py escapes the proof sandbox's granted paths", why)
        self.assertTrue(command_allowed("test -f src/../pom.xml", ALLOW, cwd="server")[0])

    def test_the_root_may_not_climb_out_of_the_checkout(self):
        self.assertFalse(command_allowed("test -f ../outside.md", ALLOW, cwd=".")[0])
        self.assertFalse(command_allowed("test -f /etc/../etc/hosts", ALLOW, cwd=".")[0])
        self.assertFalse(command_allowed("grep -q x --file=../x", ALLOW, cwd=".")[0])
        self.assertTrue(command_allowed("test -f docs/../README.md", ALLOW, cwd=".")[0])

    def test_granted_variables_climb_within_their_depth(self):
        self.assertTrue(command_allowed('python3 "$PROTOCOL_DIR/../gen.py"', ALLOW, cwd="server", var_depths=DEPTHS)[0])
        self.assertFalse(command_allowed('python3 "$PROTOCOL_DIR/../../x.py"', ALLOW, cwd="server",
                                         var_depths=DEPTHS)[0])
        self.assertFalse(command_allowed('test -f "${JAVA_HOME}/../x"', ALLOW, cwd=".", var_depths=DEPTHS)[0])
        self.assertTrue(command_allowed("test -f ~/../me/x", ALLOW, cwd=".", var_depths=DEPTHS)[0])
        self.assertFalse(command_allowed("test -f ~/../../x", ALLOW, cwd=".", var_depths=DEPTHS)[0])

    def test_a_short_option_glued_to_its_value_is_judged_by_the_value(self):
        """Review finding 3: `-C..` hid its `..` from the sandbox."""
        for cmd in ("git -C.. log", "git -C../client log", "grep -f../secret x"):
            with self.subTest(cmd=cmd):
                ok, why = command_allowed(cmd, ALLOW, cwd="server")
                self.assertFalse(ok)
                self.assertIn("escapes the proof sandbox", why)
        self.assertFalse(command_allowed("git -C.. log", ALLOW, cwd=".")[0])
        self.assertFalse(command_allowed("grep -f$HOME/../x y", ALLOW, cwd=".")[0])
        self.assertTrue(command_allowed("git -Csrc log", ALLOW, cwd="server")[0])
        self.assertTrue(command_allowed("grep -rn x src", ALLOW, cwd="server")[0])

    def test_a_value_after_equals_is_judged_by_the_variable_rule(self):
        """Review finding 3: `--file=$HOME/../x` was resolved as a relative path and passed."""
        self.assertFalse(command_allowed("grep -q x --file=$HOME/../x", ALLOW, cwd=".")[0])
        self.assertFalse(command_allowed('grep -q x --file="$OTHER/../x"', ALLOW, cwd=".", var_depths=DEPTHS)[0])
        self.assertFalse(command_allowed("grep -q x --file=$HOME/../../x", ALLOW, cwd=".", var_depths=DEPTHS)[0])
        self.assertTrue(command_allowed("grep -q x --file=$HOME/../me/x", ALLOW, cwd=".", var_depths=DEPTHS)[0])
        self.assertTrue(command_allowed("grep -q x --file=$HOME/x", ALLOW, cwd=".")[0])

    def test_an_ungranted_variable_may_not_climb(self):
        self.assertFalse(command_allowed('test -f "$OTHER/../x"', ALLOW, cwd=".", var_depths=DEPTHS)[0])
        self.assertFalse(command_allowed("test -f ~/../x", ALLOW, cwd=".")[0])
        self.assertTrue(command_allowed('test -f "$OTHER/x"', ALLOW, cwd=".")[0])


if __name__ == "__main__":
    unittest.main()
