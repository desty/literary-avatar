"""Project Gutenberg에서 소설 텍스트를 다운로드."""

import re
from pathlib import Path

import requests

GUTENBERG_URLS = {
    "sherlock_holmes": "https://www.gutenberg.org/cache/epub/1661/pg1661.txt",
    "pride_and_prejudice": "https://www.gutenberg.org/cache/epub/1342/pg1342.txt",
}

DATA_DIR = Path(__file__).parent.parent.parent / "data"


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
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    resp.encoding = "utf-8"

    text = strip_gutenberg_header_footer(resp.text)
    output_path.write_text(text, encoding="utf-8")
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
