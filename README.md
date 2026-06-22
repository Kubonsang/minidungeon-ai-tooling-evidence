# MiniDungeon — Unity AI-tooling test fixture

A minimal, **copyright-safe** Unity 6 (6000.3.8f1, URP) demo project used as a test fixture for an
AI-agent Unity tooling stack:

- [`testplay-runner`](https://github.com/Kubonsang/testplay-runner) — compile + EditMode/PlayMode test runner
- [`unity-ctx`](https://github.com/Kubonsang/unity-ctx) — scene/prefab inspection & safe property mutation
- [`unity-fileid-graph`](https://github.com/Kubonsang/unity-fileid-graph) — fileID / reference-graph validation

The fixture is built only from Unity built-in primitives, generated materials, and the C# scripts
in this repo — no external assets. See [`Assets/Demo/README.md`](Assets/Demo/README.md) and
[`ASSET_POLICY.md`](ASSET_POLICY.md).

## Verified Evidence

Every claim below is produced by a reproducible script in this repo and is sanitized of local
absolute paths (shown as `<repo-root>` / `<source-project-root>`). Full per-step detail and run
dates are in the linked reports.

### 1. MiniDungeon fixture — E2E validation

Runs the documented pipeline against the fixture: `unity-ctx scene summarize` → `unity-ctx prefab
set` (dry-run) → `uyaml scene check` → `testplay run` EditMode → PlayMode.

- **Result: 5/5 steps pass** — EditMode **11/11**, PlayMode **4/4**, `uyaml errors=0`.
- Report: [docs/demo-e2e/report.md](docs/demo-e2e/report.md)
- Reproduce: `python3 tools/run_demo_e2e.py` (Unity-free subset: `python3 tools/run_demo_fast.py`)

### 2. MiniDungeon fixture — actual write-path validation

Applies a **real** `unity-ctx prefab set --write --ack-impact`, validates the mutated prefab with
`uyaml`, runs both test suites, regenerates to restore the baseline, and confirms the working tree
is byte-clean.

- **Result: 7/7 checks pass** — mutation applied & graph-validated, tests green, fixture restored
  byte-identical to baseline.
- Report: [docs/demo-e2e/apply-report.md](docs/demo-e2e/apply-report.md)
- Reproduce: `python3 tools/run_demo_apply_e2e.py`

### 3. GNF_ — real-project dogfooding evidence (testplay-runner)

Archived `.testplay` runs from a **separate, real Unity project** (`GNF_`), copied locally under
`Other_Projects_testplay/` (kept **local-only and excluded from this public repository** via
`.gitignore`) and summarized by the analyzer into the sanitized reports below.

- **Result: 30 runs** (25 passing / 5 non-passing), **5141 tests observed**; caught **3 real test
  failures** (assertion failures) and **2 build/import/bootstrap failures** (no `results.xml`,
  never reached the test-execution phase).
- Reports: [docs/dogfooding/testplay-runner-dogfooding-report.md](docs/dogfooding/testplay-runner-dogfooding-report.md)
  · [docs/dogfooding/testplay-runner-dogfooding-summary.json](docs/dogfooding/testplay-runner-dogfooding-summary.json)
- Reproduce: `python3 tools/analyze_testplay_dogfooding.py`
- **Scope & honesty:** this is **local dogfooding by the author**, not independent third-party
  adoption or production usage. It validates **`testplay-runner` only** — the archive contains **no
  `unity-ctx` or `unity-fileid-graph` logs**, so it does **not** validate those tools. The raw
  archive is retained solely as local evidence and is not presented as an external/public claim.

> Categories 1–2 validate the MiniDungeon fixture contained in this repo. Category 3 is separate,
> real-project evidence for `testplay-runner`.
