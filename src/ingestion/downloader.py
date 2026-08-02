"""Project Gutenberg에서 소설 텍스트를 다운로드."""

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

from src.characters import CHARACTERS
from src.paths import DATA_DIR

GUTENBERG_URLS = {
    spec.book_id: spec.gutenberg_url for spec in CHARACTERS.values()
}

ALLOWED_SOURCE_HOSTS = {"gutenberg.org", "www.gutenberg.org"}
MAX_SOURCE_BYTES = 25 * 1024 * 1024

def download_text(book_id: str) -> Path:
    """Gutenberg에서 텍스트를 다운로드하고 raw/ 디렉토리에 저장."""
    url = GUTENBERG_URLS[book_id]
    raw_dir = DATA_DIR / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    output_path = raw_dir / f"{book_id}.txt"
    if output_path.exists():
        print(f"[skip] Already downloaded: {output_path}")
        return output_path

    print(f"[download] {url}")
    resp = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "Avatar/0.1 (+local literary research tool)"},
    )
    resp.raise_for_status()
    final_host = (urlparse(resp.url).hostname or "").lower()
    if final_host not in ALLOWED_SOURCE_HOSTS:
        raise RuntimeError(
            f"Refusing unexpected download redirect host: {final_host or 'unknown'}"
        )
    if len(resp.content) > MAX_SOURCE_BYTES:
        raise RuntimeError(
            f"Source exceeds the {MAX_SOURCE_BYTES // (1024 * 1024)} MB limit"
        )
    resp.encoding = "utf-8"

    text = strip_gutenberg_header_footer(resp.text)
    temporary_path = output_path.with_suffix(".txt.part")
    temporary_path.write_text(text, encoding="utf-8")
    temporary_path.replace(output_path)

    metadata = {
        "book_id": book_id,
        "requested_url": url,
        "final_url": resp.url,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "stripped_text_sha256": hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest(),
        "license_url": "https://www.gutenberg.org/policy/license.html",
    }
    (raw_dir / f"{book_id}.source.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )
    print(f"[saved] {output_path} ({len(text):,} chars)")
    return output_path


def strip_gutenberg_header_footer(text: str) -> str:
    """Gutenberg 머리말/꼬리말 제거."""
    # Start marker
    start_markers = [
        "*** START OF THE PROJECT GUTENBERG EBOOK",
        "*** START OF THIS PROJECT GUTENBERG EBOOK",
        "*END*THE SMALL PRINT",
    ]
    for marker in start_markers:
        idx = text.upper().find(marker.upper())
        if idx != -1:
            # 마커 다음 줄부터
            newline = text.find("\n", idx)
            if newline != -1:
                text = text[newline + 1 :]
            break

    # End marker
    end_markers = [
        "*** END OF THE PROJECT GUTENBERG EBOOK",
        "*** END OF THIS PROJECT GUTENBERG EBOOK",
        "End of the Project Gutenberg EBook",
        "End of Project Gutenberg",
    ]
    for marker in end_markers:
        idx = text.upper().find(marker.upper())
        if idx != -1:
            text = text[:idx]
            break

    return text.strip()


if __name__ == "__main__":
    download_text("sherlock_holmes")
