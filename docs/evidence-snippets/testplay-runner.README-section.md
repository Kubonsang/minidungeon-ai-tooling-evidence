<!-- Paste into testplay-runner/README.md. Replace the TODO link before publishing. -->

## Verified evidence

`testplay-runner` is exercised by the **MiniDungeon evidence fixture**, a copyright-safe Unity demo
project used to validate the AI-agent Unity tooling workflow.

- **MiniDungeon full E2E validation** — `unity-ctx scene summarize` → `unity-ctx prefab set` (dry-run)
  → `uyaml scene check` → `testplay-runner` EditMode → PlayMode.
  Result: **5/5 steps passed** (EditMode **11/11**, PlayMode **4/4**, `uyaml errors=0`).
- **MiniDungeon actual write-path validation** — real `unity-ctx prefab set --write --ack-impact` →
  `uyaml prefab check` → EditMode → PlayMode → regenerate fixture → byte-clean restore.
  Result: **7/7 checks passed** (real mutation applied, tests green, fixture restored byte-identical).
- **GNF_ real-project dogfooding (testplay-runner only)** — archived `.testplay` runs from a separate
  real Unity project (`GNF_`): **30 archived runs** (25 passing / 5 non-passing), **5,141 tests
  observed** (5,121 passed / 3 failed / 17 skipped), including **2 build/import/bootstrap failures**.

`testplay-runner` is validated both in the MiniDungeon fixture and in local dogfooding logs from the
real Unity project `GNF_`.

The GNF_ archive is local author dogfooding evidence, not independent third-party adoption or
production usage.

See the MiniDungeon evidence repository for the full sanitized reports (`docs/demo-e2e/report.md`,
`docs/demo-e2e/apply-report.md`, `docs/dogfooding/testplay-runner-dogfooding-report.md`):
**https://github.com/Kubonsang/minidungeon-ai-tooling-evidence**
