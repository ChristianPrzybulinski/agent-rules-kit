"""session_audit.py: the KIT-056 cross-session pre-filter on synthetic Claude Code and Codex transcripts."""
import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parent.parent.parent / "tools" / "session_audit.py"
TOKEN = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
GUARD_RM = "PreToolUse:Bash hook error: ai-kit guard: rm -rf is destructive; ask the user to run or confirm it."
GUARD_PUSH = "PreToolUse:Bash hook error: ai-kit guard: git push --force is destructive; ask the user to run or confirm it."
CLAUDE_IDS = {
    "kept": "11111111-aaaa-4aaa-8aaa-111111111111",
    "excluded": "22222222-bbbb-4bbb-8bbb-222222222222",
    "titled": "33333333-cccc-4ccc-8ccc-333333333333",
    "personal": "44444444-dddd-4ddd-8ddd-444444444444",
}
CODEX_IDS = ("019a0000-1111-7000-8000-00000000000a", "019a0000-2222-7000-8000-00000000000b")


def line(data) -> str:
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False) + "\n"


def human(text):
    return line({"type": "user", "origin": {"kind": "human"}, "message": {"role": "user", "content": text}})


def assistant(text):
    return line({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}})


def bash(tool_id, command):
    block = {"type": "tool_use", "id": tool_id, "name": "Bash", "input": {"command": command}}
    return line({"type": "assistant", "message": {"role": "assistant", "content": [block]}})


def tool_error(tool_id, body):
    block = {"type": "tool_result", "tool_use_id": tool_id, "is_error": True, "content": body}
    return line({"type": "user", "message": {"role": "user", "content": [block]}})


def title(text):
    return line({"type": "custom-title", "customTitle": text})


def codex_item(item):
    return line({"type": "event_msg", "payload": {"type": "item_completed", "item": item}})


def codex_user(text):
    return codex_item({"type": "UserMessage", "content": [{"type": "text", "text": text, "text_elements": []}]})


def load_module():
    spec = importlib.util.spec_from_file_location("session_audit", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SessionAuditTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.state = self.root / "state"
        self.claude = self.root / "claude" / "projects"
        self.codex = self.root / "codex" / "sessions"
        (self.claude / "-proj").mkdir(parents=True)
        self.codex.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def claude_session(self, sid, text, mode="w"):
        path = self.claude / "-proj" / f"{sid}.jsonl"
        with open(path, mode, encoding="utf-8") as handle:
            handle.write(text)
        return path

    def codex_session(self, sid, text):
        path = self.codex / "2026" / "11" / "10" / f"rollout-2026-11-10T10-00-00-{sid}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def run_audit(self, *args, **extra_env):
        env = {key: value for key, value in os.environ.items()
               if key not in ("XDG_STATE_HOME", "CODEX_HOME", "CODEX_SQLITE_HOME")}
        env["HOME"] = str(self.root)
        env.update(extra_env)
        result = subprocess.run(
            [sys.executable, "-B", str(TOOL), "--state", str(self.state), "--claude-dir", str(self.claude),
             "--codex-dir", str(self.codex), *args],
            capture_output=True, text=True, check=False, env=env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def counts(self, *args, **extra_env):
        return json.loads(self.run_audit(*args, **extra_env).stdout)

    def extract(self):
        return json.loads(sorted(self.state.glob("extract-*.json"))[-1].read_text(encoding="utf-8"))

    def test_token_shaped_string_is_redacted(self):
        self.claude_session(CLAUDE_IDS["kept"], human(f"de novo: use o token {TOKEN} no push")
                            + assistant(f"Kit [PROPOSAL] — gap: x\nEvidence: key {TOKEN}"))
        self.counts()
        extract = self.extract()
        text = json.dumps(extract)
        self.assertNotIn(TOKEN, text)
        self.assertIn("<redacted", extract["owner"][0]["t"])
        self.assertIn("<redacted", extract["kit"][0]["t"])
        extract_path = sorted(self.state.glob("extract-*.json"))[-1]
        self.assertEqual(stat.S_IMODE(extract_path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.state.stat().st_mode), 0o700)

    def test_excluded_and_personal_sessions_are_skipped(self):
        self.state.mkdir()
        (self.state / "exclude.txt").write_text(f"# private\n{CLAUDE_IDS['excluded'][:8]}\npessoal\n")
        self.claude_session(CLAUDE_IDS["kept"], human("de novo, rode os testes"))
        self.claude_session(CLAUDE_IDS["excluded"], human("de novo, rode os testes"))
        self.claude_session(CLAUDE_IDS["titled"], title("Pessoal — viagem") + human("de novo, rode os testes"))
        self.claude_session(CLAUDE_IDS["personal"], human("de novo: preciso do extrato do banco antes do pix"))
        counts = self.counts()
        self.assertEqual(counts["skipped_sessions"], 3)
        self.assertEqual(counts["sessions"], 1)
        self.assertEqual({entry["s"] for entry in self.extract()["owner"]}, {CLAUDE_IDS["kept"]})

    def test_late_personal_message_removes_session_from_older_extract(self):
        path = self.claude_session(CLAUDE_IDS["personal"], human("de novo, rode os testes"))
        self.counts()
        self.assertEqual(len(self.extract()["owner"]), 1)
        first = sorted(self.state.glob("extract-*.json"))[-1]
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(human("meu salario caiu"))
        time.sleep(1.1)
        self.assertEqual(self.counts()["skipped_sessions"], 1)
        self.assertEqual(json.loads(first.read_text(encoding="utf-8"))["owner"], [])
        self.assertEqual(stat.S_IMODE(first.stat().st_mode), 0o600)

    def test_late_personal_session_leaves_no_error_or_guard_in_older_extract(self):
        failure = "make: *** No rule to make target 'viagem-lisboa'."
        self.claude_session(CLAUDE_IDS["kept"], tool_error("toolu_k1", failure))
        path = self.claude_session(CLAUDE_IDS["personal"], tool_error("toolu_p1", failure)
                                   + bash("toolu_p2", "rm -rf build/") + tool_error("toolu_p2", GUARD_RM))
        self.counts()
        first = sorted(self.state.glob("extract-*.json"))[-1]
        before = json.loads(first.read_text(encoding="utf-8"))
        self.assertEqual((before["errors"][0]["sessions"], before["guard"][0]["blocks"]), (2, 1))
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(human("meu salario caiu"))
        time.sleep(1.1)
        self.assertEqual(self.counts()["skipped_sessions"], 1)
        after = json.loads(first.read_text(encoding="utf-8"))
        self.assertEqual((after["errors"], after["guard"], after["sessions"]), ([], [], 1))
        self.assertNotIn("viagem", first.read_text(encoding="utf-8"))
        self.assertNotIn(CLAUDE_IDS["personal"], first.read_text(encoding="utf-8"))

    def test_codex_message_starting_with_markup_is_checked_for_personal_words(self):
        self.codex_session(CODEX_IDS[0], codex_user("# notas\nmeu salario caiu") + codex_user("errado de novo"))
        self.codex_session(CODEX_IDS[1], codex_user("<p>meu holerite</p>") + codex_user("errado de novo"))
        counts = self.counts()
        self.assertEqual((counts["skipped_sessions"], counts["sessions"]), (2, 0))
        self.assertEqual(self.extract()["owner"], [])

    def test_keyword_added_later_applies_to_sessions_already_read(self):
        self.claude_session(CLAUDE_IDS["kept"], human("de novo, rode os testes") + human("vou para Lisboa amanha"))
        self.counts()
        first = sorted(self.state.glob("extract-*.json"))[-1]
        self.assertEqual(len(json.loads(first.read_text(encoding="utf-8"))["owner"]), 1)
        (self.state / "keywords.txt").write_text("lisboa\n", encoding="utf-8")
        time.sleep(1.1)
        counts = self.counts()
        self.assertEqual((counts["skipped_sessions"], counts["sessions"]), (1, 0))
        self.assertEqual(json.loads(first.read_text(encoding="utf-8"))["owner"], [])

    def test_resumed_old_session_is_checked_from_its_start(self):
        path = self.claude_session(CLAUDE_IDS["personal"], human("meu salario caiu"))
        month_ago = time.time() - 30 * 86400
        os.utime(path, (month_ago, month_ago))
        self.assertEqual(self.counts()["files_read"], 0)
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(human("de novo, rode os testes"))
        counts = self.counts()
        self.assertEqual((counts["skipped_sessions"], counts["sessions"]), (1, 0))
        self.assertEqual(self.extract()["owner"], [])

    def kept_then_gone(self, text):
        """Run 1 reads a session, its transcript leaves the disk, run 2 sees no file: returns run 1's extract."""
        path = self.claude_session(CLAUDE_IDS["kept"], human(text))
        self.counts()
        first = sorted(self.state.glob("extract-*.json"))[-1]
        self.assertEqual(len(json.loads(first.read_text(encoding="utf-8"))["owner"]), 1)
        path.unlink()
        time.sleep(1.1)
        self.counts()
        time.sleep(1.1)
        return first

    def test_excluded_id_reaches_kept_session_whose_transcript_is_gone(self):
        first = self.kept_then_gone("de novo, rode os testes")
        offsets = json.loads((self.state / "offsets.json").read_text(encoding="utf-8"))
        self.assertIn(CLAUDE_IDS["kept"], offsets)
        (self.state / "exclude.txt").write_text(CLAUDE_IDS["kept"][:8] + "\n", encoding="utf-8")
        self.assertEqual(self.counts()["skipped_sessions"], 1)
        self.assertEqual(json.loads(first.read_text(encoding="utf-8"))["owner"], [])
        self.assertNotIn(CLAUDE_IDS["kept"], first.read_text(encoding="utf-8"))

    def test_excluded_id_reaches_kept_session_without_offset_record(self):
        first = self.kept_then_gone("de novo, rode os testes")
        offsets_path = self.state / "offsets.json"
        offsets = json.loads(offsets_path.read_text(encoding="utf-8"))
        del offsets[CLAUDE_IDS["kept"]]
        offsets_path.write_text(json.dumps(offsets), encoding="utf-8")
        (self.state / "exclude.txt").write_text(CLAUDE_IDS["kept"][:8] + "\n", encoding="utf-8")
        self.assertEqual(self.counts()["skipped_sessions"], 1)
        self.assertEqual(json.loads(first.read_text(encoding="utf-8"))["owner"], [])

    def test_keyword_change_purges_kept_session_whose_transcript_is_gone(self):
        first = self.kept_then_gone("de novo, rode os testes")
        (self.state / "keywords.txt").write_text("lisboa\n", encoding="utf-8")
        self.assertEqual(self.counts()["skipped_sessions"], 1)
        self.assertEqual(json.loads(first.read_text(encoding="utf-8"))["owner"], [])
        self.assertNotIn(CLAUDE_IDS["kept"], first.read_text(encoding="utf-8"))

    def test_no_private_leftovers_after_a_failed_write(self):
        module = load_module()
        self.state.mkdir()
        target = self.state / "extract-20200101T000000Z.json"
        with self.assertRaises(TypeError):
            module.write_private(target, {"bad": object()})
        self.assertEqual(sorted(p.name for p in self.state.iterdir()), [])
        (self.state / "index-20200101T000000Z.json").write_text("{}", encoding="utf-8")
        (self.state / "extract-20200102T000000Z.json.tmp").write_text("{}", encoding="utf-8")
        self.counts()
        names = sorted(p.name for p in self.state.iterdir())
        self.assertFalse([n for n in names if n.endswith(".tmp") or n == "index-20200101T000000Z.json"], names)

    def test_codex_titles_from_sqlite_home_and_unreadable_database(self):
        import sqlite3
        db_home = self.root / "codex-db"
        db_home.mkdir()
        with sqlite3.connect(db_home / "state_5.sqlite") as con:
            con.execute("create table threads (id text primary key, title text, name text)")
            con.execute("insert into threads values (?, ?, ?)", (CODEX_IDS[0], "Pessoal — viagem", ""))
        con.close()
        self.state.mkdir()
        (self.state / "exclude.txt").write_text("pessoal\n", encoding="utf-8")
        self.codex_session(CODEX_IDS[0], codex_user("errado de novo"))
        counts = self.counts(CODEX_SQLITE_HOME=str(db_home))
        self.assertEqual((counts["skipped_sessions"], counts["sessions"]), (1, 0))
        (self.codex.parent / "state_5.sqlite").write_bytes(b"not a database" * 100)
        self.codex_session(CODEX_IDS[1], codex_user("errado de novo"))
        time.sleep(1.1)
        counts = self.counts()
        self.assertEqual((counts["sessions"], counts["codex_deferred"]), (0, 1))
        self.assertEqual(self.extract()["owner"], [])

    def test_keyword_recheck_runs_while_codex_titles_are_unreadable(self):
        self.codex_session(CODEX_IDS[0], codex_user("errado de novo em Lisboa"))
        self.counts()
        first = sorted(self.state.glob("extract-*.json"))[-1]
        self.assertEqual(len(json.loads(first.read_text(encoding="utf-8"))["owner"]), 1)
        (self.state / "exclude.txt").write_text("zzzzzzzz-unrelated\n", encoding="utf-8")
        (self.state / "keywords.txt").write_text("lisboa\n", encoding="utf-8")
        (self.codex.parent / "state_5.sqlite").write_bytes(b"not a database" * 100)
        time.sleep(1.1)
        self.assertEqual(self.counts()["skipped_sessions"], 1)
        self.assertEqual(json.loads(first.read_text(encoding="utf-8"))["owner"], [])

    def test_deferred_new_codex_rollout_is_read_later(self):
        self.state.mkdir()
        (self.state / "exclude.txt").write_text("zzzzzzzz-unrelated\n", encoding="utf-8")
        database = self.codex.parent / "state_5.sqlite"
        database.write_bytes(b"not a database" * 100)
        self.codex_session(CODEX_IDS[0], codex_user("errado de novo"))
        self.assertEqual(self.counts()["codex_deferred"], 1)
        database.unlink()
        time.sleep(1.1)
        counts = self.counts()
        self.assertEqual((counts["files_read"], counts["sessions"], counts["codex_deferred"]), (1, 1, 0))

    def test_codex_titles_from_config_sqlite_home(self):
        import sqlite3
        db_home = self.root / "configured-db"
        db_home.mkdir()
        with sqlite3.connect(db_home / "state_5.sqlite") as con:
            con.execute("create table threads (id text primary key, title text)")
            con.execute("insert into threads values (?, ?)", (CODEX_IDS[0], "Pessoal — viagem"))
        con.close()
        (self.codex.parent / "config.toml").write_text(f'model = "x"\nsqlite_home = "{db_home}"\n', encoding="utf-8")
        self.state.mkdir()
        (self.state / "exclude.txt").write_text("pessoal\n", encoding="utf-8")
        self.codex_session(CODEX_IDS[0], codex_user("errado de novo"))
        counts = self.counts()
        self.assertEqual((counts["skipped_sessions"], counts["sessions"]), (1, 0))

    def test_codex_titles_from_index_and_state_database_are_excluded(self):
        import sqlite3
        home = self.codex.parent
        (home / "session_index.jsonl").write_text(line({"id": CODEX_IDS[0], "thread_name": "Pessoal — viagem",
                                                        "updated_at": "2026-11-01T00:00:00Z"}), encoding="utf-8")
        with sqlite3.connect(home / "state_5.sqlite") as con:
            con.execute("create table threads (id text primary key, title text, name text)")
            con.execute("insert into threads values (?, ?, ?)", (CODEX_IDS[1], "rode os testes", "Finanças da casa"))
        con.close()
        self.state.mkdir()
        (self.state / "exclude.txt").write_text("pessoal\nfinancas\n", encoding="utf-8")
        for sid in CODEX_IDS:
            self.codex_session(sid, codex_user("errado de novo"))
        self.claude_session(CLAUDE_IDS["kept"], human("de novo, rode os testes"))
        counts = self.counts()
        self.assertEqual((counts["skipped_sessions"], counts["sessions"]), (2, 1))
        self.assertEqual({entry["s"] for entry in self.extract()["owner"]}, {CLAUDE_IDS["kept"]})

    def test_work_meaning_keyword_without_confirming_word_does_not_skip(self):
        self.claude_session(CLAUDE_IDS["kept"], human("de novo: o banco de dados caiu e o banco está lento")
                            + human("foi um investimento de tempo, de novo"))
        counts = self.counts()
        self.assertEqual(counts["skipped_sessions"], 0)
        self.assertEqual(counts["sessions"], 1)
        self.assertEqual(len(self.extract()["owner"]), 2)

    def test_second_run_reads_no_old_lines(self):
        path = self.claude_session(CLAUDE_IDS["kept"], human("de novo, rode os testes") + assistant("ok"))
        old = self.claude_session(CLAUDE_IDS["excluded"], human("de novo, rode os testes"))
        month_ago = time.time() - 30 * 86400
        os.utime(old, (month_ago, month_ago))
        first = self.counts()
        self.assertEqual((first["files"], first["files_read"], first["lines"]), (2, 1, 2))
        second = self.counts()
        self.assertEqual((second["files_read"], second["lines"], second["owner_msgs"]), (0, 0, 0))
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(human("errado, de novo") + '{"type":"user","partial')
        third = self.counts()
        self.assertEqual((third["lines"], third["owner_cues"]), (1, 1))
        with open(path, "a", encoding="utf-8") as handle:
            handle.write('"}\n')
        self.assertEqual(self.counts()["lines"], 1)

    def test_codex_rollout_is_parsed(self):
        for sid in CODEX_IDS:
            self.codex_session(sid, "".join([
                line({"type": "session_meta", "payload": {"id": sid, "cwd": "/w"}}),
                codex_user("# AGENTS.md instructions\nsempre rode tudo de novo"),
                codex_user("<environment_context>de novo</environment_context>"),
                codex_user(f"errado de novo {sid[-2:]}"),
                codex_item({"type": "AgentMessage", "content": [{"type": "Text", "text": "Kit [PROPOSAL] — gap: y"}]}),
                line({"type": "response_item", "payload": {"type": "message", "role": "assistant",
                                                           "content": [{"type": "output_text",
                                                                        "text": "Kit [PROPOSAL] — gap: y"}]}}),
                codex_item({"type": "CommandExecution", "command": ["bash", "-lc", "make"], "exit_code": 2,
                            "status": "failed", "aggregated_output": "make: *** No rule to make target 'x'.\n"}),
            ]))
        counts = self.counts()
        self.assertEqual(counts["sessions"], 2)
        extract = self.extract()
        self.assertEqual(sorted(entry["s"] for entry in extract["owner"]), sorted("cx-" + sid for sid in CODEX_IDS))
        self.assertEqual(len(extract["kit"]), 2)
        self.assertEqual(extract["errors"][0]["sessions"], 2)

    def test_blocked_rm_rf_is_classed_by_target(self):
        self.claude_session(CLAUDE_IDS["kept"], "".join([
            bash("toolu_a1", 'd=$(mktemp -d) && f="$d/out" && cd "$d" && rm -rf "$f"'),
            tool_error("toolu_a1", GUARD_RM),
            bash("toolu_b2", "rm -rf build/ 2>/dev/null"),
            tool_error("toolu_b2", GUARD_RM),
            bash("toolu_c3", "rm -rf /private/tmp/claude-501/x/scratchpad/out"),
            tool_error("toolu_c3", [{"type": "text", "text": GUARD_RM}]),
            bash("toolu_d4", "git push --force origin x"),
            tool_error("toolu_d4", GUARD_PUSH),
        ]))
        counts = self.counts()
        self.assertEqual(counts["guard_blocks"], 4)
        guard = {entry["kind"]: entry for entry in self.extract()["guard"]}
        self.assertEqual({k: guard["rm -rf"][k] for k in ("blocks", "sessions", "temp", "other")},
                         {"blocks": 3, "sessions": 1, "temp": 2, "other": 1})
        self.assertEqual((guard["git push --force"]["temp"], guard["git push --force"]["other"]), (0, 0))
        self.assertEqual(self.extract()["errors"], [])

    def test_password_in_prose_is_redacted(self):
        module = load_module()
        for text in ("my password is hunter2!", "a senha é hunter2!", "token = hunter2!", "a senha do wifi é hunter2",
                     "the token for prod is hunter2", "password is 'hunter 2'", 'password: "hunter 2"', "password: is hunter2"):
            redacted = module.redact(text)
            self.assertNotIn("hunter", redacted, text)
            self.assertNotIn(" 2", redacted, text)

    def test_target_classes(self):
        module = load_module()
        cases = {
            ('rm -rf "$TMPDIR/x"', "rm"): "temp",
            ('/bin/rm -rf "$HOME/x"', "rm"): "other",
            ("rm -rf /tmp/a ./b", "rm"): "other",
            ('t="${TMPDIR:-/tmp}/k"; rm -rf -- "$t"', "rm"): "temp",
            ('x=$(pwd); rm -rf "$x"', "rm"): "other",
            ('find "$TMPDIR/x" -name "*.o" -delete', "find"): "temp",
            ("find . -delete", "find"): "other",
            ("rm -rf 'unbalanced", "rm"): "other",
            ("rm -rf /tmpfoo", "rm"): "other",
            ('rm -rf "$TMPDIRX/a"', "rm"): "other",
            ("rm -rf /tmp", "rm"): "temp",
            ('rm -rf "${TMPDIR:+/}"', "rm"): "other",
            ("rm -rf /tmp/../etc", "rm"): "other",
            ('rm -rf "${TMPDIR-/tmp}/x"', "rm"): "temp",
        }
        for (command, tool), expected in cases.items():
            self.assertEqual(module.classify_targets(command, tool), expected, command)

    def test_memory_entries_are_counted(self):
        memory = self.claude / "-proj" / "memory"
        memory.mkdir()
        (memory / "MEMORY.md").write_text("- [Rule](compact-at-200k.md)\n")
        (memory / "compact-at-200k.md").write_text("x\n")
        read = {"type": "tool_use", "id": "toolu_m1", "name": "Read",
                "input": {"file_path": str(memory / "compact-at-200k.md")}}
        for sid in (CLAUDE_IDS["kept"], CLAUDE_IDS["titled"]):
            self.claude_session(sid, assistant("per compact-at-200k the window stays")
                                + line({"type": "assistant", "message": {"role": "assistant", "content": [read]}}))
        self.counts()
        entry = self.extract()["memory"][0]
        self.assertEqual((entry["slug"], entry["cited"], entry["read"], entry["written"]), ("compact-at-200k", 2, 2, 0))

    def test_stdout_holds_only_counts(self):
        self.claude_session(CLAUDE_IDS["kept"], human(f"de novo {TOKEN}") + human("o banco caiu"))
        self.claude_session(CLAUDE_IDS["personal"], human("meu holerite"))
        for result in (self.run_audit(), self.run_audit("--if-older-days", "7")):
            lines = result.stdout.splitlines()
            self.assertEqual(len(lines), 1)
            counts = json.loads(lines[0])
            self.assertTrue(all(isinstance(value, (int, float)) for value in counts.values()), counts)
            for secret in (TOKEN, "banco", "holerite", str(self.root), CLAUDE_IDS["kept"][:8], "personal"):
                self.assertNotIn(secret, result.stdout)
        self.assertEqual(json.loads(lines[0])["ran"], 0)


if __name__ == "__main__":
    unittest.main()
