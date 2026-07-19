"""Tests for prompt invariants and isolated Claude CLI invocation."""

import unittest
from unittest.mock import patch

from src.character.prompt_builder import build_system_prompt
from src.claude_cli import call_claude, parse_json_response


class PromptTests(unittest.TestCase):
    def test_role_era_and_language_rules_are_present(self):
        prompt = build_system_prompt(
            {"name": "Sherlock Holmes"},
            "story context",
            "conversation context",
        )

        self.assertIn("modern technology", prompt)
        self.assertIn("Do NOT mention being an AI", prompt)
        self.assertIn("same language the user uses", prompt)


class ClaudeCLITests(unittest.TestCase):
    def test_call_uses_tool_free_nonpersistent_mode(self):
        class SuccessfulResult:
            returncode = 0
            stdout = "OK\n"
            stderr = ""

        with patch("src.claude_cli.subprocess.run", return_value=SuccessfulResult()) as run:
            response = call_claude("hello", system_prompt="system")

        command = run.call_args.args[0]
        self.assertEqual(response, "OK")
        self.assertIn("--safe-mode", command)
        self.assertIn("--no-session-persistence", command)
        self.assertEqual(command[command.index("--tools") + 1], "")
        self.assertEqual(command[command.index("--system-prompt") + 1], "system")

    def test_json_parser_accepts_fenced_objects_and_arrays(self):
        self.assertEqual(
            parse_json_response('```json\n{"ok": true}\n```', expected_type=dict),
            {"ok": True},
        )
        self.assertEqual(
            parse_json_response("Result: [1, 2, 3]", expected_type=list),
            [1, 2, 3],
        )


if __name__ == "__main__":
    unittest.main()
