"""Tests for writable data-directory seeding."""

import tempfile
import unittest
from pathlib import Path

from src.paths import _seed_builtin_assets


class DataPathTests(unittest.TestCase):
    def test_packaged_assets_seed_once_without_overwriting_user_changes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "packaged"
            target = root / "user-data"
            (source / "profiles").mkdir(parents=True)
            (source / "profiles" / "character.json").write_text(
                '{"name": "packaged"}',
                encoding="utf-8",
            )

            _seed_builtin_assets(source, target)
            target_file = target / "profiles" / "character.json"
            self.assertEqual(
                target_file.read_text(encoding="utf-8"),
                '{"name": "packaged"}',
            )

            target_file.write_text('{"name": "user edit"}', encoding="utf-8")
            _seed_builtin_assets(source, target)
            self.assertEqual(
                target_file.read_text(encoding="utf-8"),
                '{"name": "user edit"}',
            )


if __name__ == "__main__":
    unittest.main()
