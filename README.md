# Avatar

**English** | [한국어](README.ko.md)

Timeline-aware, source-grounded chat with literary characters.

Avatar turns legally usable novels into local-first character chatbots. It
retrieves source passages, lets the reader choose how far into the story a
character has lived, and can save optional conversation memory between sessions.

> **Local-first, not fully local:** source files, indexes, and memories stay in
> the configured data directory. The default Claude backend sends prompts and
> selected source excerpts to an external model through the Claude Code CLI.
> See [Privacy and data flow](docs/privacy.md) before using private material.

## Features

- Chat with Sherlock Holmes or Elizabeth Bennet from the CLI.
- Restrict retrieval and prompt context to a story or chapter boundary.
- Ground answers in SQLite FTS5/BM25 passages from the source work.
- Combine profiles, relationships, narrative state, and behavioral guidance.
- Inspect and delete optional plaintext local conversation memory.
- Run the plumbing without an account using a deterministic mock backend.

Timeline control is a spoiler-reduction guardrail, not a formal guarantee. A
model can still rely on prior knowledge or infer later events.

## Quick start

### Requirements

- Python 3.11–3.13
- For real responses: Claude Code CLI installed and authenticated (`claude -p`)
- Network access for first-time source downloads

### Install with uv

```bash
uv sync
uv run avatar-prepare --all
uv run avatar
```

### Install with pip

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
avatar-prepare --all
avatar
```

`uv.lock` is the reproducible dependency resolution used for development and
release checks. `requirements.txt` remains a compatibility entry point.

### Offline plumbing demo

The mock backend makes no model request and labels its fixed response:

```bash
avatar --backend mock
# or: AVATAR_GENERATION_BACKEND=mock avatar
```

It validates runtime wiring but intentionally cannot generate new profiles,
timelines, or behavior assets.

## Prepare built-in characters

The repository includes small prepared profile, timeline, and behavior files.
Build the untracked local source text and search indexes with:

```bash
avatar-prepare --all
```

The command downloads the work, removes the Gutenberg wrapper, parses it,
builds a local SQLite FTS5 index, and generates missing analysis assets. Existing
assets are reused unless `--force-llm` is passed. Use `--skip-llm` to download,
parse, and index without an external generation call.

## Use the CLI

```bash
avatar
```

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

## Verify a checkout

```bash
python -m unittest discover -s tests -v
python scripts/smoke_check.py
python scripts/check_provenance.py
python -m build
```

On a checkout without downloaded source data, use
`python scripts/smoke_check.py --assets-only` to verify only the bundled files.

With Claude CLI authenticated, optional live checks are available:

```bash
python scripts/quality_check.py
```

## Built-in characters

| Character | Work | Timeline units | Tracked prepared assets |
| --- | --- | ---: | --- |
| Sherlock Holmes | *The Adventures of Sherlock Holmes* | 12 stories | profile, arc, behavior rules |
| Elizabeth Bennet | *Pride and Prejudice* | 61 chapters | profile, arc, behavior rules |

Downloaded books and search indexes are never tracked. See
[Data sources](DATA_SOURCES.md) and [Third-party notices](THIRD_PARTY_NOTICES.md)
for provenance, jurisdiction, model-download, and license details.

## Data locations and deletion

By default a source checkout stores generated state below `./data`. An installed
wheel copies built-in assets to the operating system's user data directory
(`~/Library/Application Support/Avatar` on macOS or
`$XDG_DATA_HOME/avatar`/`~/.local/share/avatar` on Linux). Set
`AVATAR_DATA_DIR` to choose another visible, writable location.

```text
data/raw/        downloaded source text
data/processed/ parsed source text
data/vectordb/  local SQLite full-text search index
data/memory/    plaintext conversations, summaries, and inferred user facts
```

All four directories are ignored by Git. `/forget` clears memory for the active
character/user. Removing the configured data directory deletes all locally
generated data. Review [Privacy and data flow](docs/privacy.md) for what the
generation backend may receive.

## Architecture and extension

```text
source -> parser -> timeline-tagged units -> SQLite FTS5 index
                  -> prepared profile / arc / behavior assets

message -> bounded retrieval -> prompt -> GenerationBackend -> reply
```

`GenerationBackend` currently has Claude CLI and deterministic mock
implementations. The registry in `src/characters.py` is the single source of
truth for built-in works. See [Architecture](docs/architecture.md) and
[Character builder](docs/character-builder.md).

The supported product surface is currently the CLI. A production web client
and API will be developed separately instead of bundling a prototype web UI in
this repository.

Historical research notes, evaluations, and a paper draft live in
`archive/research/`. They are not current product claims.

## Contributing and security

Read [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and the
[Code of Conduct](CODE_OF_CONDUCT.md). Never report private text, credentials,
conversation memory, or unpatched vulnerability details in a public issue.
Maintainers should complete the [public release checklist](docs/release-checklist.md)
before tagging a version.

## License

Code and documentation are MIT licensed. Prepared generated data is offered
under CC0-1.0 to the extent contributors hold rights in it. Underlying works,
quotations, third-party packages, models, services, and trademarks retain their
own status and terms. The repository is REUSE 3.3 compliant; see `REUSE.toml`
and `LICENSES/`.
