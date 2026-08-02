"""Local full-text retrieval with SQLite FTS5 and BM25 ranking."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Optional

from src.paths import DATA_DIR


DB_DIR = DATA_DIR / "vectordb"
DB_PATH = DB_DIR / "avatar-search.sqlite3"


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[dict]:
    """Split text into overlapping word chunks."""
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append({
            "text": " ".join(chunk_words),
            "start_word": start,
            "end_word": min(end, len(words)),
        })
        start += chunk_size - overlap

    return chunks


def _connect() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    _ensure_schema(connection)
    return connection


def _ensure_schema(connection: sqlite3.Connection) -> None:
    try:
        connection.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(
                book_id UNINDEXED,
                doc_id UNINDEXED,
                story_number UNINDEXED,
                story_title UNINDEXED,
                text,
                tokenize='unicode61'
            )
            """
        )
    except sqlite3.OperationalError as exc:
        raise RuntimeError(
            "This Python build does not include SQLite FTS5 support. "
            "Install an official Python 3.11+ build with FTS5 enabled."
        ) from exc

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS index_metadata (
            book_id TEXT PRIMARY KEY,
            source_sha256 TEXT NOT NULL,
            chunk_count INTEGER NOT NULL,
            indexed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def build_index(book_id: str = "sherlock_holmes", force: bool = False) -> int:
    """Build or refresh a book's local FTS5 index and return its chunk count."""
    processed = DATA_DIR / "processed" / f"{book_id}.json"
    if not processed.exists():
        raise FileNotFoundError(
            f"Missing processed source: {processed}. "
            f"Run scripts/prepare_character.py first."
        )

    source_hash = hashlib.sha256(processed.read_bytes()).hexdigest()
    data = json.loads(processed.read_text(encoding="utf-8"))

    with _connect() as connection:
        existing = connection.execute(
            "SELECT source_sha256, chunk_count FROM index_metadata WHERE book_id = ?",
            (book_id,),
        ).fetchone()
        if existing and not force and existing["source_sha256"] == source_hash:
            print(f"[skip] Search index '{book_id}' is up to date")
            return int(existing["chunk_count"])

        rows = []
        for story in data["stories"]:
            text = re.sub(r"\s+", " ", story["text"])
            for index, chunk in enumerate(
                chunk_text(text, chunk_size=400, overlap=80)
            ):
                rows.append((
                    book_id,
                    f"s{story['number']:02d}_c{index:04d}",
                    story["number"],
                    story["title"],
                    chunk["text"],
                ))

        print(f"[indexing] {len(rows)} chunks from {len(data['stories'])} stories...")
        connection.execute("DELETE FROM chunks WHERE book_id = ?", (book_id,))
        connection.executemany(
            """
            INSERT INTO chunks(book_id, doc_id, story_number, story_title, text)
            VALUES (?, ?, ?, ?, ?)
            """,
            rows,
        )
        connection.execute(
            """
            INSERT INTO index_metadata(book_id, source_sha256, chunk_count)
            VALUES (?, ?, ?)
            ON CONFLICT(book_id) DO UPDATE SET
                source_sha256 = excluded.source_sha256,
                chunk_count = excluded.chunk_count,
                indexed_at = CURRENT_TIMESTAMP
            """,
            (book_id, source_hash, len(rows)),
        )

    print(f"[done] Indexed {len(rows)} chunks with SQLite FTS5")
    return len(rows)


def _fts_query(query: str) -> str:
    tokens = list(dict.fromkeys(
        token.lower()
        for token in re.findall(r"[^\W_]+", query, flags=re.UNICODE)
        if len(token) > 1
    ))
    return " OR ".join(f'"{token.replace(chr(34), chr(34) * 2)}"' for token in tokens[:20])


def search(
    query: str,
    book_id: str = "sherlock_holmes",
    n_results: int = 5,
    max_story_number: Optional[int] = None,
) -> list[dict]:
    """Search indexed chunks while enforcing an optional story boundary."""
    if n_results <= 0:
        return []

    match_query = _fts_query(query)
    with _connect() as connection:
        indexed = connection.execute(
            "SELECT 1 FROM index_metadata WHERE book_id = ?",
            (book_id,),
        ).fetchone()
        if not indexed:
            raise RuntimeError(
                f"No local search index for {book_id}. "
                "Run scripts/prepare_character.py first."
            )

        timeline_sql = ""
        timeline_params = []
        if max_story_number is not None:
            timeline_sql = " AND CAST(story_number AS INTEGER) <= ?"
            timeline_params.append(max_story_number)

        rows = []
        if match_query:
            rows = connection.execute(
                f"""
                SELECT doc_id, story_number, story_title, text, bm25(chunks) AS score
                FROM chunks
                WHERE chunks MATCH ? AND book_id = ?{timeline_sql}
                ORDER BY score
                LIMIT ?
                """,
                (match_query, book_id, *timeline_params, n_results),
            ).fetchall()

        # A query in another language or with no lexical overlap should still
        # receive bounded source context rather than silently broadening scope.
        if not rows:
            rows = connection.execute(
                f"""
                SELECT doc_id, story_number, story_title, text, NULL AS score
                FROM chunks
                WHERE book_id = ?{timeline_sql}
                ORDER BY CAST(story_number AS INTEGER), doc_id
                LIMIT ?
                """,
                (book_id, *timeline_params, n_results),
            ).fetchall()

    return [
        {
            "id": row["doc_id"],
            "text": row["text"],
            "metadata": {
                "story_number": int(row["story_number"]),
                "story_title": row["story_title"],
            },
            "distance": row["score"],
        }
        for row in rows
    ]


if __name__ == "__main__":
    build_index()
    for query in ("Holmes deduction", "Watson", "violin"):
        print(f"\n=== Query: {query} ===")
        for result in search(query, n_results=2):
            print(f"  [{result['metadata']['story_title']}] {result['text'][:150]}...")
