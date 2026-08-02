"""Installed character preparation command."""

from __future__ import annotations

import argparse

from src.characters import CHARACTERS
from src.generation import get_generation_backend
from src.paths import DATA_DIR


def asset_exists(kind: str, character_id: str) -> bool:
    return (DATA_DIR / kind / f"{character_id}.json").exists()


def prepare_character(
    character_id: str,
    force_llm: bool = False,
    skip_llm: bool = False,
    force_index: bool = False,
    backend_name: str = None,
) -> None:
    """Run the asset preparation pipeline for one built-in character."""
    from src.character.arc_tracker import generate_arc_snapshots, save_arc
    from src.character.logic_extractor import extract_character_logic, save_logic
    from src.ingestion.downloader import download_text
    from src.ingestion.parser import parse_novel, save_parsed_novel
    from src.ingestion.profile_extractor import extract_and_save
    from src.memory.retriever import build_index

    spec = CHARACTERS[character_id]
    book_id = spec.book_id
    character_name = spec.name

    print(f"\n=== Preparing {character_name} ({character_id}) ===")
    raw_path = download_text(book_id)
    novel = parse_novel(book_id, raw_path.read_text(encoding="utf-8"))
    save_parsed_novel(novel, book_id)
    build_index(book_id, force=force_index)

    if skip_llm:
        print("[skip] LLM asset generation skipped")
        return

    generation_backend = get_generation_backend(backend_name)

    if force_llm or not asset_exists("profiles", character_id):
        extract_and_save(
            character_id,
            generation_backend=generation_backend,
        )
    else:
        print(f"[skip] Profile already exists for {character_id}")

    if force_llm or not asset_exists("arcs", character_id):
        snapshots = generate_arc_snapshots(
            book_id,
            character_name,
            generation_backend=generation_backend,
        )
        save_arc(snapshots, character_id)
    else:
        print(f"[skip] Timeline snapshots already exist for {character_id}")

    if force_llm or not asset_exists("logic", character_id):
        logic = extract_character_logic(
            book_id,
            character_name,
            generation_backend=generation_backend,
        )
        save_logic(logic, character_id)
    else:
        print(f"[skip] Behavioral guidance already exists for {character_id}")


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Avatar character assets.")
    parser.add_argument(
        "character",
        nargs="?",
        choices=sorted(CHARACTERS),
        help="Character id to prepare.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Prepare every built-in character.",
    )
    parser.add_argument(
        "--force-llm",
        action="store_true",
        help="Regenerate profile, timeline, and behavior files.",
    )
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Only download, parse, and index text. Do not call a model.",
    )
    parser.add_argument(
        "--force-index",
        action="store_true",
        help="Rebuild the search index even when the source is unchanged.",
    )
    parser.add_argument(
        "--backend",
        choices=("claude", "mock"),
        help=(
            "Generation backend. The mock backend cannot create analysis "
            "assets and is intended only for runtime tests."
        ),
    )
    return parser.parse_args(argv)


def main(argv=None) -> None:
    args = parse_args(argv)
    if not args.all and not args.character:
        raise SystemExit("Choose a character or pass --all.")

    targets = sorted(CHARACTERS) if args.all else [args.character]
    for character_id in targets:
        prepare_character(
            character_id,
            force_llm=args.force_llm,
            skip_llm=args.skip_llm,
            force_index=args.force_index,
            backend_name=args.backend,
        )


if __name__ == "__main__":
    main()
