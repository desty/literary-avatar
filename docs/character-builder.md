# Character Builder

Use `scripts/prepare_character.py` to rebuild the prepared assets for a supported character.

```bash
python3 scripts/prepare_character.py sherlock_holmes
python3 scripts/prepare_character.py elizabeth_bennet
python3 scripts/prepare_character.py --all
```

## Pipeline

1. **Download** the novel text from Project Gutenberg.
2. **Parse** the text into story or chapter units.
3. **Index** the processed text in ChromaDB.
4. **Extract profile** with identity, personality, speech, values, and relationships.
5. **Generate timeline snapshots** for story-aware knowledge boundaries.
6. **Generate behavioral guidance** used by the prompt builder.

## Supported Characters

The current builder supports:

- `sherlock_holmes`
- `elizabeth_bennet`

Adding a new character requires entries in:

- `src/ingestion/downloader.py` for the source URL.
- `src/ingestion/parser.py` for parsing rules.
- `src/ingestion/profile_extractor.py` for character extraction settings.
- `src/character/arc_tracker.py` for timeline generation settings.
- `src/character/logic_extractor.py` for behavioral guidance settings.
- `src/character/engine.py` for character-to-book mapping.

## Practical Notes

Profile, timeline, and behavior extraction use Claude CLI and can be slow. Existing files are reused by default. Use `--force-llm` only when you intentionally want to regenerate those assets.

The vector index is rebuilt automatically when the processed novel changes. Use
`--force-index` to rebuild it explicitly even when the source hash is unchanged.
