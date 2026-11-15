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



EXPANSION = "expansion the proof check cannot predict: quote it or name the path"


class UnpredictableExpansions(unittest.TestCase):
    """Review B3, second round: bash has more ways to make `..` than a list of spellings holds, so under the sandbox a
    word is judged only when its expansion is predictable: single-quoted text is literal; in unquoted or double-quoted
    text only a leading `$NAME`, `${NAME}` or `~/` anchor followed by `/` or the end is accepted."""

    def refused(self, cmd, why, depths=None):
        ok, message = command_allowed(cmd, ALLOW, cwd="server", var_depths=depths)
        self.assertFalse(ok, cmd)
        self.assertIn(why, message, cmd)

    def test_a_bundled_short_option_cluster_is_judged_at_every_suffix(self):
        self.refused("grep -rf../client/secret src", "escapes the proof sandbox")

    def test_ansi_c_and_locale_quoting_are_refused(self):
        self.refused("grep -q x $'..'/client/secret", EXPANSION)
        self.refused('git -C $".." log', EXPANSION)

    def test_brace_expansion_is_refused(self):
        self.refused("grep -q x {..,.}/client/secret", EXPANSION)
        self.refused("git -C ..{,} log", EXPANSION)
        self.refused("grep -q x src/{a..c}.txt", EXPANSION)

    def test_parameter_operators_are_refused_even_for_a_granted_variable(self):
        self.refused("test -f ${HOME:-}/../x", EXPANSION, DEPTHS)
        self.refused("test -f ${HOME%/}/../x", EXPANSION, DEPTHS)
        self.refused('test -f "$HOME$OTHER"/x', EXPANSION, DEPTHS)
        self.refused("grep -f$HOME/x y", EXPANSION, DEPTHS)

    def test_tilde_forms_other_than_home_are_refused(self):
        self.refused("test -f ~+/x", EXPANSION, DEPTHS)
        self.refused("test -f ~root/x", EXPANSION, DEPTHS)

    def test_a_glob_that_could_match_dot_or_dotdot_is_refused(self):
        for cmd in ("grep -r x .*", "grep -q x .?/client/secret", "grep -r x .[.]/client", "grep -r x src/[.]*/x"):
            with self.subTest(cmd=cmd):
                self.refused(cmd, EXPANSION)

    def test_predictable_words_still_pass(self):
        for cmd in ("grep -qE '^v[0-9]+$|a{1,2}|.*|$HOME|${X:-y}' src/a.txt", "grep -q 'a..b' src/a.txt",
                    "grep -q '\\.\\./' src/a.txt", 'grep -q "two words" src/a.txt', "grep -r x src/*.java",
                    "test -f .gitignore", "grep -q x src/{}", 'test -f "$PROTOCOL_DIR/gen.py"',
                    "test -f ${PROTOCOL_DIR}/../gen.py", "test -f ~/x", "grep -q x --file=$HOME/../me/x"):
            with self.subTest(cmd=cmd):
                self.assertEqual(command_allowed(cmd, ALLOW, cwd="server", var_depths=DEPTHS), (True, ""), cmd)

    def test_a_quoted_dotdot_component_is_still_a_path(self):
        """Quoting stops expansion, not the read: `grep -f '../x'` reads outside, and a word cannot be told from a
        pattern, so a whole `..` component is judged however it is quoted (`'a..b'` above is no component)."""
        self.refused("grep -q x -f '../client/secret'", "escapes the proof sandbox")
        self.refused("grep -q '..' src/a.txt", "escapes the proof sandbox")


if __name__ == "__main__":
    unittest.main()
