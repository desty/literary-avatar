# Privacy and data flow

Avatar is local-first, not fully local or fully offline.

## What stays on the machine

By default a source checkout uses `./data`; a wheel installation uses the
operating system's user data directory. `AVATAR_DATA_DIR` can select a different
visible, writable directory. Packaged profiles, arcs, and behavior files are
copied there once and are never allowed to overwrite user-modified files.

- Downloaded source text: `data/raw/`
- Parsed text: `data/processed/`
- SQLite FTS5 search index: `data/vectordb/`
- Conversation turns, summaries, and inferred user facts: `data/memory/`

These paths are ignored by Git. `/forget` deletes all memory layers for the
current character and user. Deleting the configured data directory removes all
locally generated source, index, and memory data.

## What can leave the machine

With the default `claude` backend, Avatar sends prompts to the locally installed
Claude Code CLI. Depending on the operation, a prompt can contain:

- the user's current message and recent conversation;
- retrieved passages from the source work;
- character profiles, relationships, and timeline state;
- locally stored conversation summaries and inferred user facts;
- excerpts used to build profiles, timelines, and behavioral guidance.

If a non-ASCII question has no lexical source match, Avatar may make an
additional backend call to rewrite that question as a short query in the source
language. If a bounded draft names a future-only entity, Avatar may make one
additional backend call to repair the draft. Both calls can include the current
user message; the repair call can also include the rejected draft and blocked
entity names.

The repository disables Claude coding tools and session persistence for each
call, but transport, retention, account, and service behavior remain governed
by the installed CLI and provider terms.

Use `AVATAR_GENERATION_BACKEND=mock` or `avatar --backend mock` to prevent model
network requests. The mock backend is for plumbing tests and does not create
real character assets.

## First-run downloads

Preparing a character downloads the selected source from Project Gutenberg.
The SQLite FTS5/BM25 search index is built locally and does not download an
embedding model.

## Sensitive content

Do not process confidential manuscripts or personal transcripts unless you
have reviewed every configured backend and accepted its data handling. Timeline
controls reduce story spoilers; they are not an access-control mechanism.
