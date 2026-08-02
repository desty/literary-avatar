# Third-party notices

Avatar's Python dependencies are declared in `pyproject.toml` and resolved in
`uv.lock`. Their upstream licenses continue to apply; the project's MIT license
does not replace them.

## External services and tools

- **Claude Code CLI** is an optional runtime prerequisite for the default
  generation backend. It is not distributed by this repository. Its service
  terms and privacy policy apply when prompts are submitted.
- **Project Gutenberg** hosts the source editions used by the built-in
  downloader. The repository does not redistribute the downloaded raw books.
  Project Gutenberg's license, trademark rules, and the user's local copyright
  law still apply.
- **SQLite FTS5** is provided by the user's Python/SQLite distribution. Avatar
  uses it for local BM25-ranked retrieval without downloading an embedding
  model or starting a database server.

See `DATA_SOURCES.md` for work-level provenance and links. Release maintainers
should review the resolved dependency license inventory before every tagged
release.
