"""Streamlit application smoke tests."""

import unittest

from streamlit.testing.v1 import AppTest


class StreamlitAppTests(unittest.TestCase):
    def test_app_renders_memory_controls_without_exceptions(self):
        app = AppTest.from_file("app.py", default_timeout=20).run()

        self.assertEqual(list(app.exception), [])
        self.assertIn("🗑️ Delete Local Memories", [button.label for button in app.button])
        self.assertIn("Confirm memory deletion", [box.label for box in app.checkbox])


if __name__ == "__main__":
    unittest.main()
