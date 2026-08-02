# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/) and
the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Standard Python packaging and an `avatar` console command.
- Deterministic offline mock backend and pluggable generation interface.
- Data provenance, privacy, security, contribution, and citation documentation.
- Cross-version CI, dependency updates, and repository templates.
- Boundary-tagged episodic recall, cross-language query rewriting after lexical
  misses, `/sources` retrieval traces, and a future-entity response guard.

### Changed

- Retrieval misses now remain empty instead of substituting unrelated early-book
  chunks as evidence.
- Cross-language replies now prefer idiomatic phrasing and avoid unsolicited
  source-language glosses.

### Removed

- Prototype Streamlit UI and its dependency tree; the CLI remains the supported
  interactive product surface while a production web client and API are designed
  separately.

### Security

- Explicit disclosure of external model data flow and local memory paths.
- Bounded responses now receive deterministic tagged-entity verification with a
  single repair attempt and safe fallback.

## [0.1.0] - Unreleased

- Initial public alpha with Sherlock Holmes and Elizabeth Bennet.
