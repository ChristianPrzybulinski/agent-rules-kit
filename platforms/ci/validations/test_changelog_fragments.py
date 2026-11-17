"""changelog_fragments.py (KIT-084): `changelog.d/<id>.<type>.md` fragments move into CHANGELOG.md → ## [Unreleased],
and every malformed line of every fragment is named in one failure before anything is written; `--check` validates
them and writes nothing. Ported from a consumer project's consolidator with its assertions, so the kit tool keeps the
output that one had."""
import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LAYER = "unit"  # KIT-077 layer (platforms/tools/run_tests.py): in-process, a throwaway folder, no subprocess or git

KIT = Path(__file__).resolve().parents[3]
TOOL = KIT / "platforms" / "ci" / "validations" / "changelog_fragments.py"
_SPEC = importlib.util.spec_from_file_location("changelog_fragments_under_test", TOOL)
fragments = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(fragments)

LOG = "# Changelog\n\n## [Unreleased]\n\n## [0.1.0]\n- x\n"


class Folder(unittest.TestCase):
    """A throwaway checkout with changelog.d/ and CHANGELOG.md."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "changelog.d").mkdir()

    def fragment(self, name, text):
        path = self.root / "changelog.d" / name
        if isinstance(text, bytes):
            path.write_bytes(text)
        else:
            path.write_text(text, encoding="utf-8")

    def log(self, text=None):
        path = self.root / "CHANGELOG.md"
        if text is not None:
            path.write_text(text, encoding="utf-8")
        return path.read_text(encoding="utf-8")

    def left(self):
        return sorted(p.name for p in (self.root / "changelog.d").iterdir())


class Consolidate(Folder):
    def test_fragments_join_their_sections_and_are_deleted(self):
        self.fragment("README.md", "rules")
        self.fragment("94.added.md", "- added thing\n")
        self.fragment("fix-x.fixed.md", "- fixed thing\n")
        self.log("# Changelog\n\n## [Unreleased]\n\n### Added\n- old\n\n## [0.1.0]\n- x\n")
        out = fragments.consolidate_changelog(self.root)
        text = self.log()
        self.assertEqual(out, {"fragments": ["94.added.md", "fix-x.fixed.md"], "entries": 2})
        self.assertIn("### Added\n- added thing\n- old", text)
        self.assertIn("### Fixed\n- fixed thing", text)
        self.assertLess(text.index("### Fixed"), text.index("## [0.1.0]"))
        self.assertEqual(self.left(), ["README.md"])

    def test_a_missing_section_is_created_in_the_keep_a_changelog_order(self):
        for name in ("1.security.md", "2.added.md", "3.removed.md", "4.changed.md", "5.deprecated.md", "6.fixed.md"):
            self.fragment(name, f"- {name}\n")
        self.log(LOG)
        fragments.consolidate_changelog(self.root)
        text = self.log()
        heads = [f"### {k}" for k in ("Added", "Changed", "Deprecated", "Removed", "Fixed", "Security")]
        self.assertEqual([text.index(h) for h in heads], sorted(text.index(h) for h in heads))
        self.assertLess(text.index("### Security"), text.index("## [0.1.0]"))

    def test_no_fragment_writes_nothing_and_reports_none(self):
        self.fragment("README.md", "rules")
        self.log(LOG)
        self.assertEqual(fragments.consolidate_changelog(self.root), {"fragments": [], "entries": 0})
        self.assertEqual(self.log(), LOG)

    def test_no_changelog_folder_reports_none(self):
        (self.root / "changelog.d").rmdir()
        self.log(LOG)
        self.assertEqual(fragments.consolidate_changelog(self.root), {"fragments": [], "entries": 0})

    def test_a_wrapped_bullet_keeps_its_lines(self):
        # keeping only the `- ` lines once dropped every wrapped line of a fragment from CHANGELOG.md
        self.fragment("94.fixed.md", "- first bullet wraps\n  over a second line\n\tand a tabbed third\n\n- second bullet\n")
        self.log("# Changelog\n\n## [Unreleased]\n\n### Fixed\n- old\n\n## [0.1.0]\n- x\n")
        out = fragments.consolidate_changelog(self.root)
        self.assertEqual(out["entries"], 2)
        self.assertIn("### Fixed\n- first bullet wraps\n  over a second line\n\tand a tabbed third\n"
                      "- second bullet\n- old\n", self.log())

    def test_a_stray_fragment_line_fails_before_writing(self):
        for text, line in (("- bullet\nnot indented\n", 2), ("  indented before any bullet\n", 1)):
            with self.subTest(text=text):
                self.fragment("1.added.md", "- fine\n")
                self.fragment("fix-x.fixed.md", text)
                self.log(LOG)
                with self.assertRaises(SystemExit) as err:
                    fragments.consolidate_changelog(self.root)
                self.assertIn(f"changelog.d/fix-x.fixed.md:{line}:", str(err.exception))
                self.assertEqual(self.log(), LOG)
                self.assertEqual(self.left(), ["1.added.md", "fix-x.fixed.md"])

    def test_every_malformed_fragment_is_named_in_one_exit(self):
        # naming only the first bad fragment once took one repair pull request per fragment
        self.fragment("1.added.md", "Added a thing without a bullet.\n")
        self.fragment("2.fixed.md", "- fine\n")
        self.fragment("3.changed.md", "one\n\ntwo\n")
        self.log(LOG)
        with self.assertRaises(SystemExit) as err:
            fragments.consolidate_changelog(self.root)
        text = str(err.exception)
        self.assertTrue(text.startswith("3 malformed fragment line(s), nothing written:"), text)
        for ref in ("changelog.d/1.added.md:1:", "changelog.d/3.changed.md:1:", "changelog.d/3.changed.md:3:"):
            self.assertIn(ref, text)
        self.assertNotIn("2.fixed.md", text)
        self.assertEqual(self.log(), LOG)
        self.assertEqual(len(self.left()), 3)

    def test_a_fragment_that_is_not_utf8_is_named_not_decoded(self):
        self.fragment("latin.fixed.md", b"- caf\xe9\n")
        self.log("# Changelog\n\n## [Unreleased]\n")
        with self.assertRaises(SystemExit) as err:
            fragments.consolidate_changelog(self.root)
        self.assertEqual(str(err.exception),
                         "1 malformed fragment line(s), nothing written:\nchangelog.d/latin.fixed.md:1: not UTF-8")

    def test_a_file_without_a_fragment_name_is_named_not_deleted(self):
        """The consumer's tool deleted a `changelog.d/*.md` whose name has no known type without moving its bullets."""
        self.fragment("1.added.md", "- fine\n")
        self.fragment("notes.md", "- would be lost\n")
        self.fragment("2.feature.md", "- unknown type\n")
        self.log(LOG)
        with self.assertRaises(SystemExit) as err:
            fragments.consolidate_changelog(self.root)
        text = str(err.exception)
        self.assertTrue(text.startswith("2 malformed fragment line(s), nothing written:"), text)
        for name in ("2.feature.md", "notes.md"):
            self.assertIn(f"changelog.d/{name}:1: not a fragment name: <id>.<type>.md, <type> one of added, changed, "
                          "deprecated, removed, fixed, security", text)
        self.assertEqual(self.log(), LOG)
        self.assertEqual(self.left(), ["1.added.md", "2.feature.md", "notes.md"])

    def test_a_changelog_without_an_unreleased_line_is_named_and_nothing_moves(self):
        """Without a `## [Unreleased]` line the consumer's tool raised a ValueError, and with one at the end of the file
        and no newline after it, it deleted the fragments and wrote none of their bullets."""
        for log in ("# Changelog\n\n## [0.1.0]\n- x\n", "# Changelog\n\n## [Unreleased]"):
            with self.subTest(log=log):
                self.fragment("1.added.md", "- fine\n")
                self.log(log)
                with self.assertRaises(SystemExit) as err:
                    fragments.consolidate_changelog(self.root)
                self.assertEqual(str(err.exception), "CHANGELOG.md has no `## [Unreleased]` line, nothing written")
                self.assertEqual(self.log(), log)
                self.assertEqual(self.left(), ["1.added.md"])

    def test_no_changelog_file_is_named(self):
        self.fragment("1.added.md", "- fine\n")
        with self.assertRaises(SystemExit) as err:
            fragments.consolidate_changelog(self.root)
        self.assertEqual(str(err.exception), "CHANGELOG.md is missing, nothing written")
        self.assertEqual(self.left(), ["1.added.md"])


class Check(Folder):
    """--check: the same verdict as a consolidation, and nothing written."""

    def test_valid_fragments_are_counted_and_stay(self):
        self.fragment("94.added.md", "- one\n- two\n")
        self.fragment("fix-x.fixed.md", "- three\n  wraps\n")
        self.log(LOG)
        self.assertEqual(fragments.check(self.root), {"fragments": ["94.added.md", "fix-x.fixed.md"], "entries": 3})
        self.assertEqual(self.log(), LOG)
        self.assertEqual(self.left(), ["94.added.md", "fix-x.fixed.md"])

    def test_malformed_fragments_fail_with_every_line_named(self):
        self.fragment("1.added.md", "bare\n")
        self.fragment("2.fixed.md", "- fine\nflush\n")
        self.log(LOG)
        with self.assertRaises(SystemExit) as err:
            fragments.check(self.root)
        text = str(err.exception)
        self.assertTrue(text.startswith("2 malformed fragment line(s), nothing written:"), text)
        self.assertIn("changelog.d/1.added.md:1:", text)
        self.assertIn("changelog.d/2.fixed.md:2:", text)
        self.assertEqual(self.left(), ["1.added.md", "2.fixed.md"])

    def test_a_changelog_the_consolidation_cannot_write_fails_the_check(self):
        self.fragment("1.added.md", "- fine\n")
        self.log("# Changelog\n")
        with self.assertRaises(SystemExit) as err:
            fragments.check(self.root)
        self.assertEqual(str(err.exception), "CHANGELOG.md has no `## [Unreleased]` line, nothing written")

    def test_no_fragment_passes_without_a_changelog(self):
        self.assertEqual(fragments.check(self.root), {"fragments": [], "entries": 0})


class ParseFragment(unittest.TestCase):
    def test_keeps_wrapped_lines_and_numbers_each_stray_line(self):
        self.assertEqual(fragments.parse_fragment("- a\n  wraps\n\n- b\n"), (["- a\n  wraps", "- b"], []))
        self.assertEqual(fragments.parse_fragment("  indented first\n- a\nflush\n")[1],
                         ["1: neither a `- ` bullet nor an indented line that wraps one: '  indented first'",
                          "3: neither a `- ` bullet nor an indented line that wraps one: 'flush'"])
        self.assertEqual(fragments.parse_fragment("\n  \n"), ([], ["1: no `- ` bullet"]))


# Python 3.9 has no sys.stdlib_module_names (3.10+), and the kit's local runs use the macOS /usr/bin/python3 3.9
# (#325). There the check uses these standard-library modules, a subset of 3.10's list (the test below proves it on
# 3.10+); a module the tool starts to import that is missing here fails on 3.9 until it is added, never the reverse.
STDLIB_FALLBACK = frozenset((
    "__future__", "abc", "argparse", "ast", "base64", "collections", "contextlib", "copy", "csv", "dataclasses",
    "datetime", "difflib", "enum", "errno", "fnmatch", "functools", "glob", "hashlib", "importlib", "io", "itertools",
    "json", "logging", "math", "operator", "os", "pathlib", "re", "shlex", "shutil", "string", "subprocess", "sys",
    "tempfile", "textwrap", "time", "typing", "unicodedata", "urllib"))


def stdlib_names():
    return frozenset(getattr(sys, "stdlib_module_names", STDLIB_FALLBACK))


class StdlibOnly(unittest.TestCase):
    """A project's CI runs the tool from $AI_KIT_DIR with the Python the spec-tools action sets up."""

    def test_it_imports_only_the_standard_library(self):
        tree = ast.parse(TOOL.read_text(encoding="utf-8"))
        names = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        names |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
        self.assertLessEqual(names, stdlib_names())

    @unittest.skipUnless(hasattr(sys, "stdlib_module_names"), "needs Python 3.10+ to compare the fallback with")
    def test_the_3_9_fallback_names_only_standard_modules(self):
        self.assertLessEqual(STDLIB_FALLBACK, frozenset(sys.stdlib_module_names))


class CommandLine(Folder):
    LAYER = "integration"  # starts the tool as a process
    COVERS = ("platforms/ci/validations/changelog_fragments.py",)

    def run_tool(self, *args):
        return subprocess.run([sys.executable, "-B", str(TOOL), *args], capture_output=True, text=True, timeout=60,
                              check=False)

    def test_it_prints_the_fragments_and_entries_as_json(self):
        self.fragment("94.added.md", "- one\n- two\n")
        self.log(LOG)
        done = self.run_tool("--repo-dir", str(self.root))
        self.assertEqual((done.returncode, done.stderr), (0, ""))
        self.assertEqual(done.stdout, json.dumps({"fragments": ["94.added.md"], "entries": 2}, indent=1) + "\n")
        self.assertEqual(self.left(), [])

    def test_a_malformed_fragment_exits_1_with_every_line_on_stderr(self):
        self.fragment("1.added.md", "bare\n")
        self.log("# Changelog\n\n## [Unreleased]\n")
        for extra in ((), ("--check",)):
            with self.subTest(args=extra):
                done = self.run_tool("--repo-dir", str(self.root), *extra)
                self.assertEqual((done.returncode, done.stdout), (1, ""))
                self.assertTrue(done.stderr.startswith("1 malformed fragment line(s), nothing written:\n"), done.stderr)
                self.assertIn("changelog.d/1.added.md:1:", done.stderr)
                self.assertEqual(self.left(), ["1.added.md"])

    def test_check_prints_the_same_json_and_writes_nothing(self):
        self.fragment("94.added.md", "- one\n")
        self.log(LOG)
        done = self.run_tool("--repo-dir", str(self.root), "--check")
        self.assertEqual((done.returncode, done.stderr), (0, ""))
        self.assertEqual(json.loads(done.stdout), {"fragments": ["94.added.md"], "entries": 1})
        self.assertEqual((self.log(), self.left()), (LOG, ["94.added.md"]))

    def test_the_repo_dir_is_required(self):
        done = self.run_tool()
        self.assertEqual(done.returncode, 2)
        self.assertIn("--repo-dir", done.stderr)


if __name__ == "__main__":
    unittest.main()
