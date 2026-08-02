# Data sources and prepared assets

Avatar tracks small prepared character assets, but not downloaded books,
processed full text, search indexes, or user conversations.

## Built-in works

| Character | Work | Author | First publication | Download source | Verified SHA-256 after header removal |
| --- | --- | --- | ---: | --- | --- |
| Sherlock Holmes | *The Adventures of Sherlock Holmes* | Arthur Conan Doyle | 1892 | Project Gutenberg ebook 1661 | `2b7238758a350af441475489c7db10b8d8e9686a3897b1acebd7e81723960f80` |
| Elizabeth Bennet | *Pride and Prejudice* | Jane Austen | 1813 | Project Gutenberg ebook 1342 | `a76e72e3976df9638aff4a6d1a9a213ca599111a359d288e1265a6d6d4ab435d` |

Source URLs are defined in `src/characters.py` and were verified on
2026-08-02. Project Gutenberg determines copyright status under United States
law. Users outside the United States must check their own jurisdiction.

## Prepared assets

Files in `data/profiles/`, `data/arcs/`, and `data/logic/` are structured
summaries generated from the works through the Claude Code CLI. They can contain
names, plot facts, and short evidence quotations. To the extent the Avatar
contributors hold rights in that generated structure, it is offered under
CC0-1.0; underlying public-domain text and third-party rights are unaffected.

The initial asset-generation run did not record the exact model identifier,
tool version, prompt revision, or generation date. That limitation is preserved
instead of guessing. `data/provenance.json` records the known hashes and marks
unknown fields explicitly. Regenerated assets must record those fields before a
release.

## Redistribution policy

- Raw and processed full text is ignored by Git and rebuilt by each user.
- Do not add a work merely because it is available online.
- Verify author death date, edition-specific material, translations,
  illustrations, and local copyright term.
- Do not imply that Project Gutenberg endorses Avatar.
- Remove Gutenberg headers and trademark material only in accordance with its
  official license and permission guidance.
