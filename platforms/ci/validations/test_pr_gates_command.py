"""pr_gates.command_allowed (KIT-073): the one proof-command predicate the PR gates, review_checks.py and
row_checks.py share — allowlist, refused constructs, the `! git diff` trap and the component rules (KIT-080)."""
import sys
import unittest
from pathlib import Path

LAYER = "unit"  # KIT-077 layer (platforms/tools/run_tests.py): in-process: no subprocess, no git

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from pr_gates import command_allowed  # noqa: E402

ALLOW = ["python3", "grep", "git", "test", "godot", "./mvnw", "!"]


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


DOTDOT = "a `..` path step"
EXPANSION = "shell expansion outside a leading $NAME, ${NAME} or ~/ anchor"
INLINE = "inline code"


class Sandbox(unittest.TestCase):
    """KIT-080 (#280, option a): with `cwd` the check is three short rules, hygiene and not isolation: no `..` path step,
    no shell expansion outside a leading `$NAME`, `${NAME}` or `~/` anchor, no interpreter given inline code."""

    def refused(self, cmd, why, cwd="server"):
        ok, message = command_allowed(cmd, ALLOW, cwd=cwd)
        self.assertFalse(ok, cmd)
        self.assertIn(why, message, cmd)

    def passes(self, cmd, cwd="server"):
        self.assertEqual(command_allowed(cmd, ALLOW, cwd=cwd), (True, ""), cmd)

    def test_any_dotdot_step_is_refused_quoted_or_not(self):
        for cmd in ("python3 ../tools/x.py", "test -f src/../pom.xml", "test -f /etc/../etc/hosts",
                    "grep -q x --file=../x", "git -C.. log", "grep -rf../client/secret src", "git show HEAD:../x",
                    'python3 "$PROTOCOL_DIR/../gen.py"', "test -f ~/../me/x", "grep -q x -f '../client/secret'",
                    "grep -q '..' src/a.txt", "grep -q x a/.."):
            with self.subTest(cmd=cmd):
                self.refused(cmd, DOTDOT)
        self.refused("test -f ../outside.md", DOTDOT, cwd=".")
        self.refused("test -f docs/../README.md", DOTDOT, cwd=".")

    def test_a_revision_range_between_letters_or_digits_is_no_dotdot_step(self):
        for cmd in ("git diff --quiet origin/main..HEAD", "git log --oneline HEAD~3..HEAD", "grep -q 'a..b' src/a.txt",
                    "grep -q '\\.\\./' src/a.txt", "test -f .../x"):
            with self.subTest(cmd=cmd):
                self.passes(cmd)

    def test_shell_expansion_is_refused_outside_a_leading_anchor(self):
        for cmd in ("grep -q x $'..'/client/secret", 'git -C $".." log', "test -f ${HOME:-}/x", "test -f ${HOME%/}/x",
                    'test -f "$HOME$OTHER"/x', "grep -f$HOME/x y", "grep -q x --file=$HOME/x", "test -f ~+/x",
                    "test -f ~root/x", "grep -q x A=x:~/y", "grep -q x --file=~/x", "git -C ..{,} log",
                    "grep -q x {..,.}/client/secret",
                    "grep -q x src/{a..c}.txt", "grep -q x src/{a,b}.txt", "grep -r x .*", "grep -q x .?/client/secret",
                    "grep -r x .[.]/client", "grep -r x src/.[a-z]*/x"):
            with self.subTest(cmd=cmd):
                self.refused(cmd, EXPANSION)

    def test_nested_braces_no_longer_hide_their_comma(self):
        """#280 known gap: the old check read only up to the first `}`, so `{{},.}.` reached `../client`."""
        for cmd in ("grep -s SECRET {{},.}./client/secret", "grep -s SECRET {{x},.}./client/secret",
                    "grep -s SECRET .{{},.}/client", "grep -s SECRET {{},..}/client",
                    "grep -s SECRET {{a},{b},.}./client"):
            with self.subTest(cmd=cmd):
                self.refused(cmd, EXPANSION)

    def test_an_interpreter_given_inline_code_is_refused(self):
        """#280 known gap: an allowlisted interpreter reads anything, so inline code is refused whatever it holds."""
        allow = ALLOW + ["bash", "sh", "env", "node", "perl", "ruby", "python3.12"]
        for cmd in ('python3 -c "print(open(chr(46)*2 + chr(47) + chr(120)).read())"', "python3 -Ic 'print(1)'",
                    "python3.12 -c 'print(1)'", "bash -c 'cat x'", "sh -ec 'cat x'", "env -S 'cat x'",
                    "env --split-string='cat x'", "node -e 'require(1)'", "node --print=1", "perl -ne 'print' x",
                    "ruby -e 'p 1'", "python3 -W ignore -c 'print(1)'", "bash -o pipefail -c 'cat x'",
                    "python3 -X dev -Ic 'print(1)'", "python3 -Wmodule -c 'print(1)'", "bash +o posix -c 'cat x'",
                    "python3 --check-hash-based-pycs never -c 'print(1)'"):
            with self.subTest(cmd=cmd):
                ok, message = command_allowed(cmd, allow, cwd="server")
                self.assertFalse(ok, cmd)
                self.assertIn(INLINE, message, cmd)
        for cmd in ("python3 -m unittest discover -s tests -p 'test_*.py'", "python3 tools/check.py --check",
                    "bash tools/run.sh", "python3 -m pytest -c pytest.ini", "python3 -Im pytest -c pytest.ini",
                    "python3 tools/check.py -c cfg.toml", "bash tools/run.sh -c", "bash -e -- tools/run.sh -c x"):
            with self.subTest(cmd=cmd):
                self.assertEqual(command_allowed(cmd, allow, cwd="server"), (True, ""), cmd)

    def test_predictable_words_still_pass(self):
        for cmd in ("grep -qE '^v[0-9]+$|a{1,2}|.*|$HOME|${X:-y}' src/a.txt", 'grep -q "two words" src/a.txt',
                    "grep -r x src/*.java", "grep -q x src/[ab].txt", "./mvnw -q test -Dtest=Trade*Test",
                    "test -f .gitignore", "grep -q x src/{}", 'test -f "$PROTOCOL_DIR/gen.py"',
                    "test -f ${PROTOCOL_DIR}/gen.py", "test -f ~/x", "test -f ~", "git diff --quiet HEAD~1",
                    "git -Csrc log", "grep -rn x src", "test -f /etc/hosts"):
            with self.subTest(cmd=cmd):
                self.passes(cmd)

    def test_the_rules_hold_only_under_a_component(self):
        for cmd in ("python3 ../tools/x.py", "python3 -c 'print(1)'", "grep -r x .*"):
            with self.subTest(cmd=cmd):
                self.assertTrue(command_allowed(cmd, ALLOW)[0], cmd)


if __name__ == "__main__":
    unittest.main()
