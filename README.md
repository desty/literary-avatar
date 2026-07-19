# Avatar

Timeline-aware chat with literary characters.

Avatar turns public-domain novels into local character chatbots. The app keeps each character grounded in the source text, lets you choose how far into the story the character has lived, and saves optional local conversation memories.

## What It Does

- Chat with Sherlock Holmes or Elizabeth Bennet from a CLI or Streamlit web UI.
- Set a story position so the character only knows events up to that point.
- Retrieve relevant passages from the novel with ChromaDB-backed RAG.
- Inject character profiles, speech patterns, relationships, narrative state, and behavioral guidance into each response.
- Store optional local memories between sessions.

Example timeline behavior:

```text
/timeline 0
You: What do you think of Irene Adler?
Holmes: That name means nothing to me.

/timeline 1
You: What do you think of Irene Adler?
Holmes: The woman outwitted me, and I do not use the phrase lightly.
```

## Quick Start

### Prerequisites

- Python 3.9+
- Claude Code CLI installed and authenticated (`claude -p`)

### Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Prepare Built-In Characters

The repository includes prepared character assets for the two built-in characters. To rebuild them from source text:

```bash
python3 scripts/prepare_character.py --all
```

This runs:

1. Download public-domain text from Project Gutenberg.
2. Parse the novel into story or chapter units.
3. Build a ChromaDB vector index.
4. Generate the character profile, timeline snapshots, and behavioral guidance.

Steps 3 and 4 can take time. The LLM-backed steps are skipped automatically when their files already exist unless you pass `--force-llm`.

Vector indexes are rebuilt automatically when the processed source changes. Pass
`--force-index` to rebuild an unchanged index explicitly.

### Run The CLI

```bash
python3 -m src.main
```

Useful commands:

```text
/switch       Switch character
/timeline 3   Limit the character to chapter/story 3
/timeline all Use full-story knowledge
/memory       Show recent local memories
/forget       Delete local memories after confirmation
/bdi          Show current mental state
/reset        Reset the conversation
/quit         Save and exit
```

### Run The Web UI

```bash
streamlit run app.py
```

### Run A Local Smoke Check

```bash
python3 scripts/smoke_check.py
```

The smoke check verifies that character profiles, timeline snapshots, behavioral guidance, and vector indexes are present.

Run the core regression tests with:

```bash
python3 -m unittest discover -s tests -v
```

With Claude CLI authenticated, run the optional live character checks with:

```bash
python3 scripts/quality_check.py
```

## Built-In Characters

| Character | Novel | Timeline Units | Prepared Assets |
| --- | --- | ---: | --- |
| Sherlock Holmes | The Adventures of Sherlock Holmes | 12 stories | profile, arc, behavior rules, RAG index |
| Elizabeth Bennet | Pride and Prejudice | 61 chapters | profile, arc, behavior rules, RAG index |

## Product Shape

Avatar is organized as a usable local product:

```text
avatar/
├── app.py                         # Streamlit chat UI
├── demo.py                        # CLI feature demo
├── scripts/
│   ├── prepare_character.py       # Rebuild character assets
│   └── smoke_check.py             # Verify local assets
├── docs/
│   ├── architecture.md            # Runtime architecture
│   ├── character-builder.md       # Character asset pipeline
│   └── product-roadmap.md         # MVP-oriented roadmap
├── src/
│   ├── main.py                    # CLI chat app
│   ├── ingestion/                 # Downloading and parsing novels
│   ├── character/                 # Character engine and prompt context
│   └── memory/                    # Session, persistent, and RAG memory
├── data/
│   ├── profiles/                  # Character profiles
│   ├── arcs/                      # Timeline snapshots
│   ├── logic/                     # Behavioral guidance
│   └── vectordb/                  # ChromaDB storage
└── archive/research/              # Archived research artifacts
```

## Notes

- Avatar uses local files for generated memories under `data/memory/`.
- The app is best with public-domain novels because the pipeline stores parsed text locally.
- Timeline control is a guardrail, not a formal guarantee. The character may still occasionally leak future knowledge, especially for very famous stories.

## License

[MIT](LICENSE)
