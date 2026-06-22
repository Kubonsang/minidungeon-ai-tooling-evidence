<!-- Paste into unity-ctx/README.md. Replace the TODO link before publishing. -->

## Verified evidence

`unity-ctx` is exercised by the **MiniDungeon evidence fixture**, a copyright-safe Unity demo project
used to validate the AI-agent Unity tooling workflow.

The MiniDungeon fixture validates `unity-ctx` in both dry-run and actual write-path workflows:

- **Full E2E validation** — `unity-ctx scene summarize`, `unity-ctx prefab set` (dry-run), fileID/YAML
  validation, and Unity EditMode/PlayMode tests.
  Result: **5/5 steps passed** (EditMode **11/11**, PlayMode **4/4**).
- **Actual write-path validation** — real `unity-ctx prefab set --write --ack-impact`, then
  validation, EditMode/PlayMode tests, fixture regeneration, and a byte-clean baseline restore.
  Result: **7/7 checks passed** (fixture restored byte-identical to baseline).

The GNF_ dogfooding archive in the MiniDungeon repository validates `testplay-runner` only; it does not
contain `unity-ctx` logs.

See the MiniDungeon evidence repository for the full sanitized reports (`docs/demo-e2e/report.md`,
`docs/demo-e2e/apply-report.md`):
**https://github.com/Kubonsang/minidungeon-ai-tooling-evidence**
