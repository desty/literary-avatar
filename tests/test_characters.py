"""Tests for the shared built-in character registry."""

import unittest

from src.characters import CHARACTERS, DEFAULT_CHARACTER_ID, get_character
from src.ingestion.downloader import GUTENBERG_URLS


class CharacterRegistryTests(unittest.TestCase):
    def test_registry_keys_match_character_ids(self):
        for character_id, spec in CHARACTERS.items():
            self.assertEqual(character_id, spec.character_id)
            self.assertEqual(GUTENBERG_URLS[spec.book_id], spec.gutenberg_url)

    def test_default_character_exists(self):
        self.assertIs(get_character(DEFAULT_CHARACTER_ID), CHARACTERS[DEFAULT_CHARACTER_ID])

    def test_unknown_character_has_useful_error(self):
        with self.assertRaisesRegex(ValueError, "Unknown character_id"):
            get_character("missing")


if __name__ == "__main__":
    unittest.main()
