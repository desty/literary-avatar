# Contributing to Avatar

Thanks for helping make source-grounded character agents easier to inspect and
reuse. Small, reviewable pull requests are preferred.

## Development setup

Avatar supports Python 3.11–3.13. With `uv`:

```bash
uv sync --extra dev
uv run avatar --backend mock
```

With `pip`:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
avatar --backend mock
```

The mock backend is deterministic and does not contact an external model. Use
the default Claude backend only after installing and authenticating the Claude
Code CLI.

## Before opening a pull request

```bash
python -m compileall -q src demo.py scripts tests
python -m unittest discover -s tests -v
python scripts/smoke_check.py
python scripts/check_provenance.py
reuse lint
pip-audit --local --skip-editable
python -m build
```

Live quality checks are optional because they require an authenticated model:

```bash
python scripts/quality_check.py
```

## Data and privacy rules

- Do not commit raw books, private uploads, conversation memories, vector
  indexes, credentials, or model session files.
- Use texts that you are legally allowed to process and redistribute in your
  jurisdiction.
- Update `DATA_SOURCES.md` and `data/provenance.json` whenever prepared assets
  or their sources change.
- Keep short source quotations only when necessary for evidence. Do not assume
  that a model-generated derivative removes the original work's restrictions.
- Describe any new network request or external model data flow in
  `docs/privacy.md`.

## Timeline-safety changes

Changes to retrieval, prompts, profiles, memory, or generated assets can leak
future events. Add a regression test that exercises a strict narrative boundary
and explain the expected failure mode in the pull request. Memory changes should
cover boundary-scoped recall; response-generation changes should exercise the
post-generation guard where applicable.

When a design is based on published research, prefer primary sources and add a
concise, non-claiming explanation to `docs/research-foundations.md`. Internal
research notes belong under the ignored `.private/` directory.

## Reporting security issues

Follow `SECURITY.md`; do not put sensitive vulnerability details in a public
issue.
