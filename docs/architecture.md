# Architecture

Avatar is a local character chat system built around four runtime contexts:

1. **Character profile**: identity, personality, speech patterns, values, relationships, habits, and reasoning style.
2. **Novel retrieval**: relevant source passages retrieved from a ChromaDB index.
3. **Timeline state**: what the character knows and does not know at a selected chapter or story position.
4. **Conversation memory**: recent session turns plus optional local summaries from prior sessions.

```text
Novel text
  -> parser
  -> processed stories/chapters
  -> vector index

Processed story units
  -> profile extractor
  -> timeline snapshot generator
  -> behavioral guidance extractor

User message
  -> timeline-filtered retrieval
  -> prompt builder
  -> isolated Claude CLI adapter
  -> character response
```

Built-in character metadata lives in `src/characters.py`. Runtime entry points
and asset-generation modules use this shared registry instead of maintaining
separate character-to-book mappings.

All LLM calls go through `src/claude_cli.py`, which disables coding tools and
session persistence and centralizes JSON response parsing.

## Timeline Control

Avatar computes one effective knowledge boundary from the character's narrative
position and the reader's progress, using whichever is earlier. The same
boundary now controls:

- ChromaDB retrieval.
- Cumulative character state and the future-unknown list.
- The system prompt's hard knowledge constraint.
- A timeline-safe projection of the full-book character profile.
- Conversation, BDI, theory-of-mind, behavioral-rule, and persistent-memory
  context that could otherwise reintroduce later plot facts.

Moving to an earlier boundary clears the active conversation and derived mental
state, because those turns may have been generated with broader knowledge.
Full-book behavioral rules and persistent episode summaries are used only when
no timeline boundary is active. This is the main product feature: a user can
talk to a character as they were at a particular point in the story.

## Memory

Avatar has two memory layers:

- **ConversationMemory** keeps recent turns inside the active session.
- **PersistentMemory** stores optional local summaries and user facts under `data/memory/`.

Active turns are journaled locally before session summarization so an interrupted CLI or
web session can be recovered. Persistent memory is intentionally local and file-based so
it is easy to inspect or delete.

## Product Boundary

Research artifacts live in `archive/research/`. Runtime code lives in `src/`,
product scripts live in `scripts/`, and user-facing docs live in `docs/`.
