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

## Adding a Character

Character metadata has one source of truth: `src/characters.py`. Add a
`CharacterSpec` containing the character ID, source book, speaker tag, display
metadata, and Project Gutenberg URL.

If the character comes from a book that is not already supported, also add a
book parser to `src/ingestion/parser.py` and register it in `PARSERS`. The
profile, timeline, behavior, UI, CLI, downloader, and RAG mapping all read from
the shared character registry automatically.

Then prepare the assets:

```bash
python3 scripts/prepare_character.py <character_id>
```

## Practical Notes

Profile, timeline, and behavior extraction use Claude CLI and can be slow.
Existing files are reused by default. Use `--force-llm` only when you
intentionally want to regenerate those assets.

The vector index is rebuilt automatically when the processed novel changes. Use
`--force-index` to rebuild it explicitly even when the source hash is unchanged.
