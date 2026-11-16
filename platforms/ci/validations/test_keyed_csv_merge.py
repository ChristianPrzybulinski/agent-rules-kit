"""keyed_csv_merge.py (KIT-074): the 3-way merge of a keyed CSV by key, as a library and as a git merge driver."""
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LAYER = "unit"  # KIT-077 layer (platforms/tools/run_tests.py): in-process: no subprocess, no git

KIT = Path(__file__).resolve().parents[3]
SCRIPT = KIT / "platforms" / "kits" / "godot" / "scripts" / "keyed_csv_merge.py"
sys.path.insert(0, str(SCRIPT.parent))
import keyed_csv_merge as kcm  # noqa: E402

HEADER = "keys,en,pt_BR\n"


def csv_text(*rows, header=HEADER):
    return header + "".join(f"{row}\n" for row in rows)


def merge(base, ours, theirs, **kwargs):
    return kcm.merge(base, ours, theirs, **kwargs)


class MergeKeys(unittest.TestCase):
    """The rule per key: o == t gives o; o == b gives t; t == b gives o; anything else is a conflict."""

    def test_a_key_edited_on_one_side_and_untouched_on_the_other_takes_the_edit(self):
        # the case merge=union got wrong: the untouched side's stale row stayed beside the edited one
        base = csv_text("account.login.submit,Play,Jogar")
        theirs = csv_text("account.login.submit,Sign in,Entrar")
        self.assertEqual(merge(base, base, theirs), (theirs, []))
        self.assertEqual(merge(base, theirs, base), (theirs, []))

    def test_keys_added_on_both_sides_are_both_kept_in_order(self):
        base = csv_text("b.key,B,B")
        merged, conflicts = merge(base, csv_text("b.key,B,B", "d.key,D,D"), csv_text("a.key,A,A", "b.key,B,B"))
        self.assertEqual((merged, conflicts), (csv_text("a.key,A,A", "b.key,B,B", "d.key,D,D"), []))

    def test_a_key_deleted_on_one_side_and_untouched_on_the_other_is_dropped(self):
        base = csv_text("a.key,A,A", "b.key,B,B")
        self.assertEqual(merge(base, csv_text("a.key,A,A"), base), (csv_text("a.key,A,A"), []))

    def test_the_same_edit_on_both_sides_is_one_row(self):
        base = csv_text("a.key,A,A")
        self.assertEqual(merge(base, csv_text("a.key,X,X"), csv_text("a.key,X,X")), (csv_text("a.key,X,X"), []))

    def test_a_side_without_the_file_counts_as_empty(self):
        self.assertEqual(merge("", "", csv_text("a.key,A,A")), (csv_text("a.key,A,A"), []))

    def test_a_row_is_kept_byte_for_byte(self):
        row = 'a.key,"Sign in, now","Entrar, já"  '
        self.assertEqual(merge("", "", csv_text(row)), (csv_text(row), []))

    def test_blank_lines_are_dropped(self):
        self.assertEqual(merge("", "", HEADER + "\na.key,A,A\n\n"), (csv_text("a.key,A,A"), []))


class Conflicts(unittest.TestCase):
    def test_a_key_edited_differently_on_both_sides_is_a_conflict_with_markers_at_its_place(self):
        base = csv_text("a.key,A,A", "b.key,B,B", "c.key,C,C")
        merged, conflicts = merge(base, csv_text("a.key,A,A", "b.key,X,X", "c.key,C,C"),
                                  csv_text("a.key,A,A", "b.key,Y,Y", "c.key,C2,C2"))
        self.assertEqual(conflicts, ["b.key"])
        self.assertEqual(merged, HEADER + "a.key,A,A\n<<<<<<< ours\nb.key,X,X\n=======\nb.key,Y,Y\n>>>>>>> theirs\n"
                         "c.key,C2,C2\n")

    def test_an_edit_against_a_delete_is_a_conflict(self):
        base = csv_text("a.key,A,A")
        merged, conflicts = merge(base, csv_text("a.key,X,X"), HEADER)
        self.assertEqual(conflicts, ["a.key"])
        self.assertEqual(merged, HEADER + "<<<<<<< ours\na.key,X,X\n=======\n>>>>>>> theirs\n")

    def test_a_key_twice_on_one_side_is_a_conflict(self):
        base = csv_text("a.key,A,A")
        merged, conflicts = merge(base, csv_text("a.key,A,A", "a.key,A,A"), base)
        self.assertEqual(conflicts, ["a.key"])
        self.assertIn("<<<<<<< ours\na.key,A,A\na.key,A,A\n=======\na.key,A,A\n>>>>>>> theirs\n", merged)

    def test_two_different_headers_are_a_conflict(self):
        base = "keys,en\na.key,A\n"
        merged, conflicts = merge(base, "keys,en,note\na.key,A\n", "keys,en,other\na.key,A\n")
        self.assertEqual(conflicts, [kcm.HEADER])
        self.assertTrue(merged.startswith("<<<<<<< ours\nkeys,en,note\n=======\nkeys,en,other\n>>>>>>> theirs\n"))

    def test_the_marker_size_and_labels_follow_the_caller(self):
        base = csv_text("a.key,A,A")
        merged, _ = merge(base, csv_text("a.key,X,X"), csv_text("a.key,Y,Y"), marker_size=9,
                          labels=("HEAD", "feature"))
        self.assertIn("<<<<<<<<< HEAD\na.key,X,X\n=========\na.key,Y,Y\n>>>>>>>>> feature\n", merged)


class Parameters(unittest.TestCase):
    def test_the_key_column_is_a_parameter(self):
        base = "en,id\nPlay,1\nQuit,2\n"
        merged, conflicts = merge(base, "en,id\nPlay now,1\nQuit,2\n", "en,id\nPlay,1\nExit,2\n", key_column=2)
        self.assertEqual((merged, conflicts), ("en,id\nPlay now,1\nExit,2\n", []))

    def test_a_quoted_key_with_a_comma_is_one_key(self):
        base = csv_text('"a,b",A,A', "c,C,C")
        merged, conflicts = merge(base, csv_text('"a,b",X,X', "c,C,C"), csv_text('"a,b",A,A', "c,C2,C2"))
        self.assertEqual((merged, conflicts), (csv_text('"a,b",X,X', "c,C2,C2"), []))

    def test_a_quoted_value_over_several_lines_is_one_row(self):
        multi = 'b.key,"line one\nline two",B'
        base = csv_text("a.key,A,A", multi)
        merged, conflicts = merge(base, csv_text("a.key,A2,A2", multi), csv_text("a.key,A,A", multi, "c.key,C,C"))
        self.assertEqual((merged, conflicts), (csv_text("a.key,A2,A2", multi, "c.key,C,C"), []))

    def test_an_unsorted_file_keeps_our_order_and_places_their_new_key_after_its_neighbour(self):
        base = csv_text("z.key,Z,Z", "a.key,A,A")
        ours = csv_text("z.key,Z,Z", "a.key,A,A", "m.key,M,M")
        theirs = csv_text("z.key,Z,Z", "q.key,Q,Q", "a.key,A,A")
        self.assertEqual(merge(base, ours, theirs), (csv_text("z.key,Z,Z", "q.key,Q,Q", "a.key,A,A", "m.key,M,M"), []))

    def test_sorted_sides_give_a_sorted_result(self):
        base = csv_text("a,A,A", "b2,B,B")
        ours = csv_text("a,A,A", "b2,B,B", "b4,B,B")
        theirs = csv_text("a,A,A", "b1,B,B", "b2,B,B", "b3,B,B")
        merged, _ = merge(base, ours, theirs)
        self.assertEqual(merged, csv_text("a,A,A", "b1,B,B", "b2,B,B", "b3,B,B", "b4,B,B"))

    def test_crlf_on_our_side_is_kept_and_compares_equal_to_lf(self):
        base = csv_text("a.key,A,A", "b.key,B,B")
        ours = base.replace("\n", "\r\n")
        theirs = csv_text("a.key,A,A", "b.key,B2,B2")
        merged, conflicts = merge(base, ours, theirs)
        self.assertEqual((merged, conflicts), (csv_text("a.key,A,A", "b.key,B2,B2").replace("\n", "\r\n"), []))

    def test_an_unbalanced_quote_is_a_parse_error(self):
        with self.assertRaises(ValueError):
            merge("", "", csv_text('a.key,"open,A'))

    def test_a_row_without_the_key_column_is_a_parse_error(self):
        with self.assertRaises(ValueError):
            merge("", "", "en,id\nPlay\n", key_column=2)


class Driver(unittest.TestCase):
    """The script as git runs it: `merge.keyed-csv.driver` in the repository config and a `.gitattributes` line."""

    LAYER = "integration"  # starts processes (scripts, git, temp repos)
    COVERS = ("platforms/kits/godot/scripts/keyed_csv_merge.py",)

    CSV = "client/i18n/strings.csv"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.git("init", "-q", "-b", "main")
        (self.repo / ".gitattributes").write_text("client/i18n/*.csv merge=keyed-csv\n", encoding="utf-8")
        self.write(csv_text("a.key,A,A", "b.key,B,B"))
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "base")
        self.git("switch", "-q", "-c", "feature")
        self.write(csv_text("a.key,A,A", "b.key,B2,B2"))
        self.git("commit", "-qam", "feature edits b")
        self.git("switch", "-q", "main")
        self.write(csv_text("a.key,A5,A5", "b.key,B,B"))
        self.git("commit", "-qam", "main edits a")

    def git(self, *args, check=True):
        env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)
        result = subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=t", "-c", "user.email=t@t",
                                 "-c", "commit.gpgsign=false", *args], capture_output=True, text=True, env=env)
        if check:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def driver(self):
        # the command the module text documents, with this interpreter and the kit path in place of the vendored copy
        command = f"{shlex.quote(sys.executable)} -B {shlex.quote(str(SCRIPT))} --marker-size %L --path %P %O %A %B"
        self.git("config", "merge.keyed-csv.name", "keyed CSV merge")
        self.git("config", "merge.keyed-csv.driver", command)

    def write(self, text):
        path = self.repo / self.CSV
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))

    def read(self):
        return (self.repo / self.CSV).read_text(encoding="utf-8")

    def test_edits_of_different_keys_merge_cleanly(self):
        self.driver()
        result = self.git("merge", "-q", "--no-edit", "feature", check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.read(), csv_text("a.key,A5,A5", "b.key,B2,B2"))

    def test_without_the_driver_git_falls_back_to_its_text_merge(self):
        # the attribute names an undefined driver: git merges as text and reports the conflict that merge=union hid
        self.git("switch", "-q", "feature")
        self.write(csv_text("a.key,A7,A7", "b.key,B2,B2"))
        self.git("commit", "-qam", "feature edits a too")
        self.git("switch", "-q", "main")
        result = self.git("merge", "-q", "--no-edit", "feature", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("<<<<<<<", self.read())

    def test_the_same_key_edited_on_both_sides_conflicts_on_that_key_only(self):
        self.git("switch", "-q", "feature")
        self.write(csv_text("a.key,A7,A7", "b.key,B2,B2"))
        self.git("commit", "-qam", "feature edits a too")
        self.git("switch", "-q", "main")
        self.driver()
        result = self.git("merge", "-q", "--no-edit", "feature", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CONFLICT", result.stdout + result.stderr)
        self.assertEqual(self.read(), HEADER + "<<<<<<< ours\na.key,A5,A5\n=======\na.key,A7,A7\n>>>>>>> theirs\n"
                         "b.key,B2,B2\n")

    def test_the_key_column_option_reaches_the_script(self):
        # keyed by id (column 2), both sides retitled row 1: a conflict; keyed by the text, two new rows merge
        files = {"base": "en,id\nPlay,1\n", "ours": "en,id\nStart,1\n", "theirs": "en,id\nGo,1\n"}
        for name, text in files.items():
            (self.repo / name).write_text(text, encoding="utf-8")
        args = [str(self.repo / name) for name in ("base", "ours", "theirs")]
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "--key-column", "2", *args],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        (self.repo / "ours").write_text(files["ours"], encoding="utf-8")
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.repo / "ours").read_text(encoding="utf-8"), "en,id\nGo,1\nStart,1\n")

    def test_an_unparsable_side_falls_back_to_a_text_merge(self):
        self.git("switch", "-q", "feature")
        self.write(csv_text('a.key,"A7,A7', "b.key,B2,B2"))
        self.git("commit", "-qam", "feature breaks a quote")
        self.git("switch", "-q", "main")
        self.driver()
        result = self.git("merge", "-q", "--no-edit", "feature", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("keyed_csv_merge: client/i18n/strings.csv:", result.stdout + result.stderr)
        self.assertIn("<<<<<<<", self.read())

    def test_a_stray_quote_merges_the_whole_file_as_text_and_warns(self):
        """#283 item 3 (KIT-079), the documented fallback: the record split reads every `"` as a quote, so an inch
        mark in an unquoted field leaves the side unparsable; the warning says the keyed merge is off and how to
        write the mark so it parses."""
        files = {"base": csv_text("a.key,A,A", "b.key,B,B"), "ours": csv_text('a.key,5" screen,A', "b.key,B,B"),
                 "theirs": csv_text("a.key,A,A", "b.key,B2,B2")}
        for name, text in files.items():
            (self.repo / name).write_text(text, encoding="utf-8")
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "--path", self.CSV,
                                 *(str(self.repo / name) for name in files)], capture_output=True, text=True)
        self.assertIn(f"keyed_csv_merge: {self.CSV}: a quoted field is not closed; warning: the whole file merges as "
                      "text, not by key", result.stderr)
        self.assertIn('"5"" screen"', result.stderr)

    def test_a_usage_error_exits_2(self):
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "only-one-file"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
