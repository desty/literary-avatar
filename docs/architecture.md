# Architecture

Avatar is a local-first character chat system built around four runtime contexts:

1. **Character profile**: identity, personality, speech patterns, values, relationships, habits, and reasoning style.
2. **Novel retrieval**: relevant source passages ranked by SQLite FTS5/BM25.
3. **Timeline state**: what the character knows and does not know at a selected chapter or story position.
4. **Conversation memory**: recent session turns plus optional local summaries from prior sessions.

```text
Novel text
  -> parser
  -> processed stories/chapters
  -> SQLite full-text index

Processed story units
  -> profile extractor
  -> timeline snapshot generator
  -> behavioral guidance extractor

User message
  -> timeline-filtered retrieval
       -> optional source-language query rewrite after a lexical miss
  -> prompt builder
  -> GenerationBackend
       -> isolated Claude CLI adapter
       -> deterministic offline mock
  -> timeline response guard
  -> character response
```

Built-in character metadata lives in `src/characters.py`. Runtime entry points
and asset-generation modules use this shared registry instead of maintaining
separate character-to-book mappings.

All model-facing features use the `GenerationBackend` interface in
`src/generation.py`. The default Claude adapter delegates to `src/claude_cli.py`,
which disables coding tools and session persistence. The mock backend supports
offline tests but does not fabricate analysis assets.

## Timeline Control

Avatar computes one effective knowledge boundary from the character's narrative
position and the reader's progress, using whichever is earlier. The same
boundary now controls:

- SQLite FTS5 retrieval.
- Cumulative character state and the future-unknown list.
- The system prompt's hard knowledge constraint.
- A timeline-safe projection of the full-book character profile.
- Boundary-tagged persistent-memory recall, while unscoped profile, BDI,
  theory-of-mind, and behavioral-rule context is omitted.

Moving to an earlier boundary clears the active conversation and derived mental
state, because those turns may have been generated with broader knowledge.
Full-book behavioral rules and unscoped legacy memories are used only when no
timeline boundary is active; compatible boundary-tagged episodes remain
available. This is the main product feature: a user can talk to a character as
they were at a particular point in the story.

## Retrieval

The default index uses Python's bundled SQLite FTS5 engine and BM25 ranking. It
stores no executable serialization and requires no database server or embedding
model. An empty result remains empty instead of being replaced by unrelated
early-book chunks. When a non-ASCII query has no match, the configured generation
backend can produce a short source-language lexical query; the second search uses
the same SQL timeline boundary. The rewritten query is not treated as evidence.
A future semantic retriever should implement the same search contract and pass
the same boundary tests before becoming an optional backend.

The engine retains a trace of the query, rewrite status, boundary, document IDs,
story positions, and excerpts used in the latest turn. The CLI exposes this trace
through `/sources` so a user can distinguish grounded retrieval from a miss.

## Memory

Avatar has two memory layers:

- **ConversationMemory** keeps recent turns inside the active session.
- **PersistentMemory** stores optional local summaries and user facts under `data/memory/`.

Every new persisted turn records the effective story/chapter boundary. An
episode spanning several boundaries inherits the least restrictive one. Bounded
recall admits only episodes whose recorded boundary is no later than the active
boundary. Legacy, unrestricted, and individually unscoped user-profile facts are
excluded from bounded recall.

Active turns are journaled locally before session summarization so an interrupted CLI
session can be recovered. Persistent memory is intentionally local and file-based so it
is easy to inspect or delete.

The default backend still sends prompt content to an external model. Local
storage does not imply local inference; see `docs/privacy.md`.

## Response guard

After a bounded response is generated, Avatar checks it for entities tagged as
first appearing after the active boundary. A detected response receives one
constrained repair attempt. If the repaired draft still contains a blocked
entity, Avatar returns a deterministic uncertainty response. This guard cannot
detect every paraphrase or untagged future fact and is not a formal guarantee.

## Product Boundary

Research artifacts live in `archive/research/`. Runtime code lives in `src/`,
product scripts live in `scripts/`, and user-facing docs live in `docs/`.
The current interactive product surface is the CLI. A production web client and
API are intentionally kept out of this repository until their integration and
deployment boundaries are defined.

See `docs/research-foundations.md` for the primary research that motivated these
invariants and for explicit non-claims.
