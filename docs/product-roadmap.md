# Product Roadmap

## MVP

- Reliable setup for the built-in characters.
- Reliable CLI chat path.
- Timeline position control with named story/chapter labels.
- Boundary-scoped conversation memory.
- Lightweight cross-language query rewriting.
- Inspectable source traces through `/sources`.
- A post-generation guard for named future entities.
- Local smoke checks for profiles, arcs, behavior rules, and search indexes.
- Clear memory controls for viewing and deleting local memories.
- Product-oriented checks for timeline leaks, anachronisms, and character voice.

## Next

- Optional multilingual semantic retrieval beyond lexical query rewriting, behind
  the existing bounded-search contract, with no remotely exposed vector database
  and a reviewed model license.
- Improve timeline selection from numeric positions to readable story/chapter selectors.
- Add era grounding for historical technologies, etiquette, and social norms.
- Add a guided character builder for new public-domain novels.
- Add broader first-run setup coverage across supported platforms.
- Define a production web architecture with a versioned API, streaming responses,
  background ingestion jobs, and explicit deployment and privacy boundaries.
- Add reproducible knowledge-boundary, long-turn persona, and emotional-fidelity
  evaluation suites.

## Later

- Support multi-character conversations inside the same novel.
- Add import/export for character packs.
- Add optional local-only model backends.
