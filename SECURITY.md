# Security Policy

## Supported versions

Until the first stable release, security fixes are made on the latest `0.x`
release and the default branch only.

## Reporting a vulnerability

Use GitHub's **Security → Report a vulnerability** private reporting flow for
the published repository. Do not open a public issue containing exploit steps,
private source text, conversation memory, credentials, or uploaded files.

Include the affected version, operating system, backend, reproduction steps,
impact, and any suggested mitigation. Maintainers will acknowledge a complete
report within seven days and will coordinate disclosure after a fix is ready.

## Security boundary

- The Claude backend launches the local `claude` executable with tools and
  session persistence disabled, but prompts are still processed by an external
  service under that service's terms.
- The mock backend performs no network model request.
- Raw texts, SQLite search indexes, and conversation memories are ignored by Git and
  stored under the configured Avatar data directory.
- Timeline safety is a prompt-and-retrieval guardrail, not a confidentiality
  boundary. Do not use it to protect secrets.
- Source documents are untrusted input. Do not follow instructions found in a
  document, and do not add tool-enabled model execution to the ingestion path.

See `docs/security-model.md` and `docs/privacy.md` for the detailed model.
