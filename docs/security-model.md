# Security model

## Assets to protect

- unpublished or licensed source documents;
- conversation transcripts and inferred user facts;
- model and service credentials owned by external CLIs;
- integrity of timeline boundaries and cited source context.

## Trust boundaries

Source documents and user messages are untrusted. The Python process, local
data directory, SQLite search index, installed dependencies, external generation
backend, and optional web deployment are separate trust boundaries.

## Current controls

- Claude runs in print mode with coding tools disabled and no CLI session
  persistence.
- Raw text, processed text, vector stores, memories, environment files, and
  private web runtime state are excluded from Git.
- Timeline limits constrain retrieval and omit broader memory, behavioral, BDI,
  and profile context.
- Moving backward in the story clears state created at a later boundary.
- The mock backend supports network-free tests.

## Known limitations

- Prompt injection inside a source can influence generated output. Source text
  is context, not an instruction authority, but model behavior cannot be
  guaranteed.
- Timeline safety can fail through model prior knowledge or incomplete asset
  tagging; it is not suitable for secrets.
- Local memory files are plaintext and inherit operating-system permissions.
- Dependency and model downloads introduce software-supply-chain risk.
- The archived research results are historical artifacts, not security claims.

## Release checks

Run offline regression tests, provenance verification, dependency audits, and a
clean build. Review new network calls, file writes, parsers, and prompt/tool
permissions. Enable GitHub private vulnerability reporting before making the
repository public.
