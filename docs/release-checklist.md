# Public release checklist

## Repository settings

- Add the intended GitHub remote and verify that both the Python and web
  repositories point to the correct owners.
- Enable private vulnerability reporting, secret scanning/push protection,
  Dependabot alerts, and branch protection requiring CI.
- Add the repository URL to `CITATION.cff` and `pyproject.toml` once it exists.
- Set a social preview, description, and focused repository topics.

## Python release

- Confirm `CHANGELOG.md`, `src.__version__`, `CITATION.cff`, and the tag agree.
- Run `uv sync --extra dev` from a clean Python 3.11–3.13 environment.
- Run unit tests, smoke check, provenance check, REUSE lint, and package build.
- Install the built wheel outside the checkout and run `avatar --version` and
  the mock backend.
- Review the resolved dependency and model license inventory.
- Confirm no raw source, processed text, vector store, memory, credential,
  environment, or build file is tracked.
- Create a signed `v0.x.y` tag and attach the wheel and source distribution.

## Web release

- Keep it in its separate repository with its own MIT license and policies.
- Apply all D1 migrations and verify owner-scoped list, upload, and deletion.
- Confirm the Sites access policy and trusted authentication-header boundary.
- Run lint, build tests, production dependency audit, and high-severity audit.
- Review accepted development-only findings in `SECURITY.md`.
- Do not describe analysis or chat as production-backed until the Python
  pipeline is connected and tested end to end.

## Final human review

- Test the quick start on a machine or account that did not create the project.
- Read the README as a first-time user and verify every claim.
- Check public-domain and edition status for every bundled character in the
  jurisdictions where the release will be distributed.
- Verify contributor names, acknowledgements, citation metadata, and release
  contact methods.
