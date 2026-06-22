# Local raw dogfooding archive

This folder is reserved for local raw `.testplay` archives copied from other Unity projects.

**Raw archives are intentionally NOT committed to the public repository** (see `.gitignore`).
They may contain local absolute paths, machine-specific logs, or large generated artifacts, so
they are kept local-only as the underlying evidence.

The public, sanitized summaries derived from these archives are committed under:

- `docs/dogfooding/testplay-runner-dogfooding-report.md`
- `docs/dogfooding/testplay-runner-dogfooding-summary.json`
- `docs/dogfooding/sanitized-samples/`

Those summaries are produced deterministically (and re-runnably) by
`tools/analyze_testplay_dogfooding.py`, which sanitizes local paths. This is **local author
dogfooding evidence for `testplay-runner` only** — not independent third-party adoption or
production usage, and it does not contain `unity-ctx` or `unity-fileid-graph` logs.
