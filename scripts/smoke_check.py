"""Verify that Avatar's prepared local assets can be loaded."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.character.engine import CharacterEngine
from src.memory.retriever import search

CHARACTERS = ("sherlock_holmes", "elizabeth_bennet")


def check_character(character_id: str) -> None:
    engine = CharacterEngine(character_id)
    if not engine.profile:
        raise RuntimeError(f"{character_id}: missing profile")
    if not engine.arc_snapshots:
        raise RuntimeError(f"{character_id}: missing timeline snapshots")
    if not engine.character_logic:
        raise RuntimeError(f"{character_id}: missing behavioral guidance")

    results = search("relationship", book_id=engine.book_id, n_results=1)
    if not results:
        raise RuntimeError(f"{character_id}: vector search returned no results")

    timeline_results = search(
        "relationship",
        book_id=engine.book_id,
        n_results=3,
        max_story_number=1,
    )
    if any(r["metadata"].get("story_number", 0) > 1 for r in timeline_results):
        raise RuntimeError(f"{character_id}: timeline-filtered search leaked future chapters")

    print(
        f"[ok] {character_id}: "
        f"{len(engine.arc_snapshots)} timeline units, "
        f"{engine.character_logic.get('total_rules', 0)} behavior rules"
    )


def main() -> None:
    for character_id in CHARACTERS:
        check_character(character_id)
    print("[ok] Avatar assets are ready.")


if __name__ == "__main__":
    main()
