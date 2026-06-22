<!-- Paste into unity-fileid-graph/README.md. Replace the TODO link before publishing. -->

## Verified evidence

`unity-fileid-graph` (`uyaml`) is exercised by the **MiniDungeon evidence fixture**, a copyright-safe
Unity demo project used to validate the AI-agent Unity tooling workflow.

The MiniDungeon fixture exercises the fileID/YAML validation layer as part of the AI-agent Unity
workflow:

- `uyaml` validates scene/prefab structure during both the full E2E run and the actual write-path run.
- Validation passes when the process exit code is `0` and `errors=0`.
- Warning-only `UNKNOWN_CLASS_ID` entries are non-fatal in the fixture reports (the tool models
  GameObject/Transform; other classes surface as warnings that also appear on genuine Unity files).

The GNF_ dogfooding archive in the MiniDungeon repository validates `testplay-runner` only; it does not
contain `unity-fileid-graph` logs.

See the MiniDungeon evidence repository for the full sanitized reports (`docs/demo-e2e/report.md`,
`docs/demo-e2e/apply-report.md`):
**https://github.com/Kubonsang/minidungeon-ai-tooling-evidence**
