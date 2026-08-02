## Summary

Describe the user-visible change and why it belongs in Avatar.

## Verification

- [ ] `python -m unittest discover -s tests -v`
- [ ] `python scripts/smoke_check.py` when assets or ingestion changed
- [ ] No credentials, private conversations, raw source files, or vector stores are committed
- [ ] Documentation and data provenance are updated when behavior or assets changed
- [ ] New dependencies and copied code have compatible licenses

## Timeline safety

Explain whether this changes retrieval, prompts, memory, or narrative boundaries.
