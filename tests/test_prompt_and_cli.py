"""Tests for prompt invariants and isolated Claude CLI invocation."""

import unittest
from unittest.mock import patch

from src.character.prompt_builder import (
    build_system_prompt,
    build_timeline_safe_profile,
)
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

    def test_timeline_safe_profile_omits_plot_outcomes_and_blocked_people(self):
        profile = {
            "name": "Test Character",
            "full_description": "Eventually learns the final secret.",
            "big_five": {"openness": 0.8},
            "speech_patterns": [
                "Uses dry wit",
                "Always jokes with Future Person",
            ],
            "values": ["Truth"],
            "relationships": {
                "Future Person": "Becomes their closest ally",
            },
            "sample_expressions": ["I know the final secret."],
            "reasoning_style": "Reasoning changed after the final revelation.",
        }

        safe = build_timeline_safe_profile(profile, ["Future Person"])
        prompt = build_system_prompt(
            safe,
            "bounded story context",
            "(No conversation history yet)",
            timeline_position=2,
        )

        self.assertIn("Uses dry wit", prompt)
        self.assertIn("Your knowledge ends at story/chapter 2", prompt)
        self.assertNotIn("Eventually learns the final secret", prompt)
        self.assertNotIn("Future Person", prompt)
        self.assertNotIn("closest ally", prompt)
        self.assertNotIn("final revelation", prompt)


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
