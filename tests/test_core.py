"""Regression tests for Avatar's core runtime behavior."""

import subprocess
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src.character.arc_tracker import (
    find_future_only_entities,
    get_future_only_entities,
)
from src.character.engine import CharacterEngine
from src.memory.persistent import PersistentMemory
from src.generation import MockBackend
from src.memory import retriever


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

    def test_reader_position_alone_builds_a_hard_knowledge_boundary(self):
        engine = self.make_engine(use_rag=False)
        engine.set_reader_position(3)
        captured = {}

        def capture_prompt(system_prompt, _user_input):
            captured["system_prompt"] = system_prompt
            return "A response"

        with patch.object(engine, "_call_claude", side_effect=capture_prompt):
            engine.respond("What happens next?")

        prompt = captured["system_prompt"]
        self.assertIn("Active Knowledge Boundary — Highest Priority", prompt)
        self.assertIn("Your knowledge ends at story/chapter 3", prompt)
        self.assertIn("CRITICAL KNOWLEDGE BOUNDARY", prompt)

    def test_strictest_boundary_controls_arc_state_as_well_as_search(self):
        engine = self.make_engine(use_rag=False)
        engine.arc_snapshots = [
            {
                "story_number": 1,
                "story_title": "Early",
                "knowledge_gained": ["early fact"],
                "emotional_state": "early state",
                "relationship_changes": {},
                "key_events": [],
            },
            {
                "story_number": 2,
                "story_title": "Late",
                "knowledge_gained": ["late fact"],
                "emotional_state": "late state",
                "relationship_changes": {},
                "key_events": [],
            },
        ]
        engine.set_narrative_position(2)
        engine.set_reader_position(1)
        captured = {}

        def capture_prompt(system_prompt, _user_input):
            captured["system_prompt"] = system_prompt
            return "A response"

        with patch.object(engine, "_call_claude", side_effect=capture_prompt):
            engine.respond("What do you know?")

        prompt = captured["system_prompt"]
        self.assertIn("story/chapter 1", prompt)
        self.assertIn("early state", prompt)
        self.assertNotIn("Your current emotional state: late state", prompt)

    def test_bounded_prompt_omits_full_book_profile_logic_and_persistent_memory(self):
        persistent = Mock()
        persistent.recall.return_value = "FUTURE MEMORY LEAK"
        engine = CharacterEngine(
            "elizabeth_bennet",
            persistent_memory=persistent,
            config={"use_rag": False, "use_logic": True, "use_tom": True},
        )
        engine.set_reader_position(10)
        captured = {}

        def capture_prompt(system_prompt, _user_input):
            captured["system_prompt"] = system_prompt
            return "A response"

        with (
            patch.object(engine, "_call_claude", side_effect=capture_prompt),
            patch(
                "src.character.engine.format_logic_for_prompt",
                return_value="FULL BOOK LOGIC LEAK",
            ) as mock_logic,
        ):
            engine.respond("Tell me about yourself")

        prompt = captured["system_prompt"]
        self.assertNotIn("Complex antagonist-to-lover dynamic", prompt)
        self.assertNotIn("FULL BOOK LOGIC LEAK", prompt)
        self.assertNotIn("FUTURE MEMORY LEAK", prompt)
        mock_logic.assert_not_called()
        persistent.recall.assert_not_called()
        persistent.save_turn.assert_called_once()

    def test_moving_to_an_earlier_boundary_clears_contaminated_state(self):
        engine = self.make_engine(use_rag=False)
        engine.set_narrative_position(5)
        engine.memory.add("user", "A later event")
        engine.memory.add("character", "A later answer")
        engine.bdi_state = {
            "beliefs": ["later belief"],
            "desires": ["later desire"],
            "intentions": ["later intention"],
        }
        engine.tom_state = {"internal_reasoning": "later reasoning"}

        engine.set_reader_position(3)

        self.assertEqual(engine.memory.messages, [])
        self.assertFalse(any(engine.bdi_state.values()))
        self.assertEqual(engine.tom_state, {})

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

    def test_injected_mock_backend_runs_without_claude(self):
        engine = CharacterEngine(
            "elizabeth_bennet",
            generation_backend=MockBackend(),
            config={"use_rag": False, "use_tom": False, "use_logic": False},
        )

        with patch("src.claude_cli.subprocess.run") as run:
            response = engine.respond("Hello")

        self.assertIn("Offline mock response", response)
        run.assert_not_called()


class ArcBoundaryTests(unittest.TestCase):
    def test_known_people_are_not_reclassified_as_future_only(self):
        snapshots = [
            {
                "story_number": 1,
                "relationship_changes": {"Known Person": "met"},
            },
            {
                "story_number": 2,
                "relationship_changes": {
                    "Known Person": "relationship changed",
                    "Future Person": "first appeared",
                },
            },
        ]

        self.assertEqual(
            get_future_only_entities(snapshots, 1),
            ["Future Person"],
        )
        self.assertEqual(
            find_future_only_entities(
                "Have you met FUTURE PERSON?",
                snapshots,
                1,
            ),
            ["Future Person"],
        )


class LocalRetrieverTests(unittest.TestCase):
    def test_sqlite_search_enforces_timeline_boundary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            processed_dir = data_dir / "processed"
            index_dir = data_dir / "vectordb"
            processed_dir.mkdir()
            source = {
                "stories": [
                    {
                        "number": 1,
                        "title": "Early",
                        "text": "Watson observes an ordinary early clue.",
                    },
                    {
                        "number": 2,
                        "title": "Late",
                        "text": "Adler reveals the final secret evidence.",
                    },
                ],
            }
            (processed_dir / "test_book.json").write_text(
                json.dumps(source),
                encoding="utf-8",
            )

            with (
                patch.object(retriever, "DATA_DIR", data_dir),
                patch.object(retriever, "DB_DIR", index_dir),
                patch.object(retriever, "DB_PATH", index_dir / "search.sqlite3"),
            ):
                self.assertEqual(retriever.build_index("test_book"), 2)
                full = retriever.search("final secret", "test_book", n_results=1)
                bounded = retriever.search(
                    "final secret",
                    "test_book",
                    n_results=2,
                    max_story_number=1,
                )

            self.assertEqual(full[0]["metadata"]["story_number"], 2)
            self.assertTrue(bounded)
            self.assertTrue(
                all(item["metadata"]["story_number"] <= 1 for item in bounded)
            )
            self.assertNotIn("final secret", bounded[0]["text"])

    def test_fts_query_treats_user_input_as_terms_not_sql(self):
        query = retriever._fts_query('\" OR 1=1 --')
        self.assertNotIn("=", query)
        self.assertEqual(query, '"or"')


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
