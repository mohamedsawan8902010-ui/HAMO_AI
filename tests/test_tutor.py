import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
os.environ["HAMO_PROVIDER"] = "mock"

import chat  # noqa: E402
import tutor  # noqa: E402


class TutorTests(unittest.TestCase):
    def test_chat_mode_leaves_message_unchanged(self):
        self.assertEqual(tutor.apply_mode("chat", "ما هو الفاعل؟"), "ما هو الفاعل؟")

    def test_every_mode_wraps_message_with_its_directive(self):
        for mode, directive in tutor.MODES.items():
            if mode == "chat":
                continue
            out = tutor.apply_mode(mode, "نص الدرس")
            self.assertIn(directive, out)
            self.assertIn("نص الدرس", out)

    def test_unknown_mode_rejected(self):
        with self.assertRaises(ValueError):
            tutor.apply_mode("hack", "x")

    def test_system_instruction_is_arabic_and_guards_against_pasted_instructions(self):
        self.assertIn("HAMO AI", tutor.SYSTEM_INSTRUCTION)
        self.assertIn("ليس تعليمات", tutor.SYSTEM_INSTRUCTION)


class ChatShapingTests(unittest.TestCase):
    def test_parse_request_defaults(self):
        message, mode, history = chat.parse_request({"message": "  مرحبا  "})
        self.assertEqual((message, mode, history), ("مرحبا", "chat", []))

    def test_parse_request_rejects_bad_input(self):
        bad = [
            [1, 2], "text", None, {}, {"message": ""}, {"message": 5},
            {"message": "x", "mode": "nope"}, {"message": "x", "mode": 3},
            {"message": "x", "history": "abc"},
            {"message": "x", "history": [1]},
            {"message": "x", "history": [{"role": "system", "text": "t"}]},
            {"message": "x", "history": [{"role": "user", "text": 5}]},
            {"message": "x" * (chat.MAX_MESSAGE_CHARS + 1)},
            {"message": "x", "history": [{"role": "user", "text": "a"}] * (chat.MAX_HISTORY_ITEMS + 1)},
        ]
        for data in bad:
            with self.subTest(data=str(data)[:40]):
                with self.assertRaises(chat.ChatError):
                    chat.parse_request(data)

    def test_history_is_normalized_for_the_model(self):
        history = [
            {"role": "assistant", "text": "orphan reply"},   # must be dropped (cannot start the chat)
            {"role": "user", "text": "q1"},
            {"role": "user", "text": "q1b"},                 # merged with q1
            {"role": "assistant", "text": "a1"},
        ]
        turns = chat.build_turns("q2", "chat", history)
        self.assertEqual([t["role"] for t in turns], ["user", "assistant", "user"])
        self.assertIn("q1b", turns[0]["text"])
        self.assertEqual(turns[-1]["text"], "q2")

    def test_mode_directive_only_on_last_turn(self):
        turns = chat.build_turns("نص", "explain", [{"role": "user", "text": "سابق"}, {"role": "assistant", "text": "رد"}])
        self.assertIn(tutor.MODES["explain"], turns[-1]["text"])
        self.assertNotIn(tutor.MODES["explain"], turns[0]["text"])

    def test_context_is_capped(self):
        big = "ع" * 11_000
        history = [{"role": "user", "text": big}, {"role": "assistant", "text": big}] * 3
        turns = chat.build_turns("سؤال", "chat", history)
        self.assertLessEqual(sum(len(t["text"]) for t in turns), chat.MAX_CONTEXT_CHARS)
        self.assertEqual(turns[0]["role"], "user")
        self.assertEqual(turns[-1]["text"], "سؤال")


if __name__ == "__main__":
    unittest.main()
