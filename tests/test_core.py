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

    def test_bounded_prompt_omits_full_book_context_and_uses_safe_memory(self):
        persistent = Mock()
        persistent.recall.return_value = "SAFE EARLY MEMORY"
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
        self.assertIn("SAFE EARLY MEMORY", prompt)
        self.assertIn("untrusted conversational recollections", prompt)
        mock_logic.assert_not_called()
        persistent.recall.assert_called_once_with(
            "Tell me about yourself",
            max_story_number=10,
        )
        persistent.save_turn.assert_called_once_with(
            "Tell me about yourself",
            "A response",
            knowledge_boundary=10,
        )

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

    def test_cross_language_miss_rewrites_query_without_broadening_boundary(self):
        class RewriteBackend:
            name = "rewrite-test"

            def generate(self, prompt, timeout=180, system_prompt=None):
                del timeout
                if system_prompt:
                    return "I must examine the evidence."
                self.rewrite_prompt = prompt
                return '{"query":"Irene Adler photograph"}'

        backend = RewriteBackend()
        engine = CharacterEngine(
            "sherlock_holmes",
            generation_backend=backend,
            config={"use_logic": False, "use_tom": False},
        )
        engine.set_narrative_position(1)
        result = {
            "id": "s01_c0001",
            "text": "Irene Adler keeps a photograph.",
            "metadata": {"story_number": 1, "story_title": "A Scandal"},
            "distance": -2.0,
        }

        with patch("src.character.engine.search", side_effect=[[], [result]]) as search_mock:
            response = engine.respond("아이린 애들러의 사진은?")

        self.assertEqual(response, "I must examine the evidence.")
        self.assertEqual(search_mock.call_count, 2)
        self.assertEqual(
            search_mock.call_args_list[1].args[0],
            "Irene Adler photograph",
        )
        self.assertEqual(
            search_mock.call_args_list[1].kwargs["max_story_number"],
            1,
        )
        self.assertTrue(engine.last_retrieval["rewritten"])
        self.assertIn("s01_c0001", engine.format_last_sources())

    def test_timeline_guard_repairs_future_entity_reference(self):
        class SequenceBackend:
            name = "sequence-test"

            def __init__(self):
                self.responses = iter([
                    "Future Person revealed the secret.",
                    "That person is unknown to me.",
                ])

            def generate(self, prompt, timeout=180, system_prompt=None):
                del prompt, timeout, system_prompt
                return next(self.responses)

        engine = CharacterEngine(
            "sherlock_holmes",
            generation_backend=SequenceBackend(),
            config={"use_rag": False, "use_logic": False, "use_tom": False},
        )
        engine.arc_snapshots = [
            {"story_number": 1, "relationship_changes": {}},
            {
                "story_number": 2,
                "relationship_changes": {"Future Person": "first appears"},
            },
        ]
        engine.set_narrative_position(1)

        response = engine.respond("Who is that person?")

        self.assertEqual(response, "That person is unknown to me.")
        self.assertEqual(engine.last_response_guard["status"], "repaired")
        self.assertNotIn("Future Person", response)

    def test_timeline_guard_uses_safe_fallback_after_failed_repair(self):
        class LeakyBackend:
            name = "leaky-test"

            def generate(self, prompt, timeout=180, system_prompt=None):
                del prompt, timeout, system_prompt
                return "Future Person knows everything."

        engine = CharacterEngine(
            "sherlock_holmes",
            generation_backend=LeakyBackend(),
            config={"use_rag": False, "use_logic": False, "use_tom": False},
        )
        engine.arc_snapshots = [
            {"story_number": 1, "relationship_changes": {}},
            {
                "story_number": 2,
                "relationship_changes": {"Future Person": "first appears"},
            },
        ]
        engine.set_narrative_position(1)

        response = engine.respond("미래 인물은 누구야?")

        self.assertNotIn("Future Person", response)
        self.assertIn("낯섭니다", response)
        self.assertEqual(engine.last_response_guard["status"], "blocked")


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
            self.assertEqual(bounded, [])

    def test_fts_query_treats_user_input_as_terms_not_sql(self):
        query = retriever._fts_query('\" OR 1=1 --')
        self.assertNotIn("=", query)
        self.assertEqual(query, "")


class PersistentMemoryTests(unittest.TestCase):
    def test_bounded_recall_filters_unscoped_and_later_episodes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("src.memory.persistent.DATA_DIR", Path(temp_dir)):
                memory = PersistentMemory("test_character")
                memory.episodes = [
                    {"date": "legacy", "summary": "legacy clue"},
                    {
                        "date": "full",
                        "summary": "full clue",
                        "knowledge_boundary": None,
                    },
                    {
                        "date": "early",
                        "summary": "early clue",
                        "knowledge_boundary": 2,
                    },
                    {
                        "date": "late",
                        "summary": "late clue",
                        "knowledge_boundary": 5,
                    },
                ]
                memory.user_profile["known_facts"] = ["private profile fact"]

                recalled = memory.recall("clue", max_story_number=3)

        self.assertIn("early clue", recalled)
        self.assertNotIn("legacy clue", recalled)
        self.assertNotIn("full clue", recalled)
        self.assertNotIn("late clue", recalled)
        self.assertNotIn("private profile fact", recalled)

    def test_episode_records_least_restrictive_session_boundary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("src.memory.persistent.DATA_DIR", Path(temp_dir)):
                memory = PersistentMemory(
                    "test_character",
                    generation_backend=MockBackend(),
                )
                memory.save_turn("First", "Reply", knowledge_boundary=2)
                memory.save_turn("Second", "Reply", knowledge_boundary=4)
                memory.end_session()

                self.assertEqual(memory.episodes[0]["knowledge_boundary"], 4)

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
