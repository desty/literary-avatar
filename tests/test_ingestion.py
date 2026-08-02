"""Tests for source download and local provenance safeguards."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src.ingestion import downloader


class DownloaderTests(unittest.TestCase):
    def response(self, url: str, text: str) -> Mock:
        response = Mock()
        response.url = url
        response.text = text
        response.content = text.encode("utf-8")
        response.raise_for_status.return_value = None
        return response

    def test_download_records_source_metadata_and_strips_wrapper(self):
        wrapped = (
            "header\n*** START OF THE PROJECT GUTENBERG EBOOK TEST ***\n"
            "Story body\n*** END OF THE PROJECT GUTENBERG EBOOK TEST ***\nfooter"
        )
        response = self.response(
            "https://www.gutenberg.org/cache/epub/1661/pg1661.txt",
            wrapped,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch.object(downloader, "DATA_DIR", Path(temp_dir)),
                patch.object(downloader.requests, "get", return_value=response),
            ):
                path = downloader.download_text("sherlock_holmes")

            metadata = json.loads(
                path.with_name("sherlock_holmes.source.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(path.read_text(encoding="utf-8"), "Story body")
            self.assertEqual(metadata["final_url"], response.url)
            self.assertEqual(len(metadata["stripped_text_sha256"]), 64)

    def test_download_rejects_redirect_outside_gutenberg(self):
        response = self.response("https://example.com/book.txt", "Story")

        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch.object(downloader, "DATA_DIR", Path(temp_dir)),
                patch.object(downloader.requests, "get", return_value=response),
            ):
                with self.assertRaisesRegex(RuntimeError, "redirect host"):
                    downloader.download_text("sherlock_holmes")

            self.assertFalse(
                (Path(temp_dir) / "raw" / "sherlock_holmes.txt").exists()
            )


if __name__ == "__main__":
    unittest.main()
