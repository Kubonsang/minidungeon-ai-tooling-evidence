# Evidence README snippets for the Unity tooling repositories

These are **ready-to-paste** "Verified evidence" sections for the three AI-agent Unity tooling
repositories, each scoped to what the MiniDungeon evidence actually proves for that tool.

> Why these live here: the tooling repos
> ([`testplay-runner`](https://github.com/Kubonsang/testplay-runner),
> [`unity-ctx`](https://github.com/Kubonsang/unity-ctx),
> [`unity-fileid-graph`](https://github.com/Kubonsang/unity-fileid-graph)) are **separate repos and
> are not present in this working tree**, so their READMEs cannot be edited from here. Copy the
> matching snippet into the corresponding repo's `README.md`.

| Repo | Snippet | Evidence categories |
|---|---|---|
| `testplay-runner` | [`testplay-runner.README-section.md`](testplay-runner.README-section.md) | Full E2E + actual write-path + GNF_ dogfooding |
| `unity-ctx` | [`unity-ctx.README-section.md`](unity-ctx.README-section.md) | Full E2E + actual write-path |
| `unity-fileid-graph` | [`unity-fileid-graph.README-section.md`](unity-fileid-graph.README-section.md) | MiniDungeon validation role |

**Before pasting:** replace `https://github.com/Kubonsang/minidungeon-ai-tooling-evidence` with the public URL of
the MiniDungeon evidence repository once it is known. (It is intentionally left as a `TODO` — the URL
is not known in this working tree and must not be invented.)

The underlying sanitized reports referenced by these snippets are:

- `docs/demo-e2e/report.md` — full E2E validation
- `docs/demo-e2e/apply-report.md` — actual write-path validation
- `docs/dogfooding/testplay-runner-dogfooding-report.md` and
  `docs/dogfooding/testplay-runner-dogfooding-summary.json` — GNF_ dogfooding (testplay-runner only)
