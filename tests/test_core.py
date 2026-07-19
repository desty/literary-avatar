"""Regression tests for Avatar's core runtime behavior."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.character.engine import CharacterEngine
from src.memory.persistent import PersistentMemory


class CharacterEngineTests(unittest.TestCase):
    def make_engine(self, **config) -> CharacterEngine:
        defaults = {
            "use_rag": True,
            "use_logic": False,
            "use_tom": False,
        }
        defaults.update(config)
        return CharacterEngine("elizabeth_bennet", config=defaults)

    def test_timeline_limit_is_applied_during_search(self):
        engine = self.make_engine()
        engine.set_narrative_position(5)
        engine.set_reader_position(3)

        with patch("src.character.engine.search", return_value=[]) as mock_search:
            with patch.object(engine, "_call_claude", return_value="A response"):
                self.assertEqual(engine.respond("Mr Darcy"), "A response")

        mock_search.assert_called_once_with(
            "Mr Darcy",
            book_id="pride_and_prejudice",
            n_results=3,
            max_story_number=3,
        )

    def test_invalid_timeline_position_is_rejected(self):
        engine = self.make_engine(use_rag=False)

        with self.assertRaises(ValueError):
            engine.set_narrative_position(-1)
        with self.assertRaises(ValueError):
            engine.set_narrative_position(len(engine.arc_snapshots) + 1)

    def test_claude_timeout_returns_error_without_saving_turn(self):
        engine = self.make_engine(use_rag=False)

        with patch(
            "src.claude_cli.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=180),
        ):
            response = engine.respond("Hello")

        self.assertIn("timed out", response)
        self.assertEqual(engine.memory.messages, [])


class PersistentMemoryTests(unittest.TestCase):
    def test_nonzero_claude_exit_preserves_fallback_episode(self):
        class FailedResult:
            returncode = 1
            stdout = ""
            stderr = "authentication failed"

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("src.memory.persistent.DATA_DIR", Path(temp_dir)):
                memory = PersistentMemory("test_character")
                memory.save_turn("Hello", "Good evening")
                self.assertTrue(memory.active_session_file.exists())

                with patch(
                    "src.claude_cli.subprocess.run",
                    return_value=FailedResult(),
                ):
                    memory.end_session()

                self.assertEqual(memory.session_buffer, [])
                self.assertEqual(len(memory.episodes), 1)
                self.assertEqual(memory.episodes[0]["turns"][0]["user"], "Hello")
                self.assertTrue(memory.episodes_file.exists())
                self.assertEqual(
                    memory._load_json(memory.active_session_file, None),
                    [],
                )

    def test_clear_all_overwrites_every_memory_layer(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("src.memory.persistent.DATA_DIR", Path(temp_dir)):
                memory = PersistentMemory("test_character")
                memory.episodes = [{"summary": "saved"}]
                memory.user_profile["known_facts"] = ["private fact"]
                memory.save_turn("Hello", "Good evening")

                memory.clear_all()

                self.assertEqual(memory.episodes, [])
                self.assertEqual(memory.user_profile["known_facts"], [])
                self.assertEqual(memory.session_buffer, [])
                self.assertEqual(memory._load_json(memory.episodes_file, None), [])


if __name__ == "__main__":
    unittest.main()
