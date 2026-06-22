# testplay-runner Dogfooding Report

## 1. Context

This evidence comes from a **real, separate Unity project** (`GNF_`) on which [`testplay-runner`](https://github.com/Kubonsang/testplay-runner) was run repeatedly during development. Its archived `.testplay/` run set was copied into this repository under `Other_Projects_testplay/` purely as dogfooding evidence.

It is **separate from the MiniDungeon fixture** in this repo: MiniDungeon is the tiny copyright-safe test fixture; `GNF_` is a real game project with a large asset set and a real test suite. Observed run dates: 20260618 – 20260622.

## 2. Summary

| Metric | Value |
|---|---:|
| Run folders found | 30 |
| Runs with summary.json | 30 |
| Passing runs | 25 |
| Non-passing runs | 5 |
| Total tests observed | 5141 |
| Total passed tests observed | 5121 |
| Total failed tests observed | 3 |
| Total skipped/inconclusive observed | 17 |
| Runs missing results.xml | 2 |
| Incomplete/malformed runs | 0 |
| Total observed runtime | 2728s |
| Longest single run | 189s |

All values above are computed directly from the archived files by `tools/analyze_testplay_dogfooding.py`.

## 3. Failure Taxonomy

### Compile / import / bootstrap failure — 2 run(s)

- Representative run folders: `20260621-193325-ed7d14b3`, `20260621-193702-02ac0810`
- Evidence (`20260621-193325-ed7d14b3`): exit_code=6, results.xml=no, reached_running=False, duration=189s — no results.xml (no NUnit document produced); phase never reached 'running' (failed before tests executed)
- Evidence (`20260621-193702-02ac0810`): exit_code=6, results.xml=no, reached_running=False, duration=189s — no results.xml (no NUnit document produced); phase never reached 'running' (failed before tests executed)
- Why it matters: Proves the runner distinguishes project-level build/import/bootstrap failures (no tests executed, no results.xml) from ordinary test failures.

### Test assertion / runtime failure — 3 run(s)

- Representative run folders: `20260618-210424-aa0d68ff`, `20260622-100533-d58b8049`, `20260622-135625-86016be8`
- Evidence: `ResetVisualState_RestoresOriginalBaseColor` → ResetVisualState 후 MPB _BaseColor가 sharedMaterial의 원본 색으로 복원되어야 한다. Expected: RGBA(0.200, 0.700, 0.400, 1.000) But was: RGBA(0.200, 0.700, 0.400, 1.000)
- Evidence: `ServerBuild_OpensStartRoomExits` → 시작룸 출구는 빌드 직후 열려 있어야 한다(스폰 즉시 stall 방지) Expected: False But was: True
- Evidence: `T5_ShopRoomHandler_GenerateChoices_ReturnsThreeDistinct` → Expected: 3 But was: 2
- Why it matters: Proves the runner surfaces genuine product bugs: a real assertion failed and was reported with the failing test name and expected/actual values.

## 4. What This Proves

- `testplay-runner` was run **30 times** against a real Unity project, not only the MiniDungeon fixture.
- It captured **25 passing runs** (e.g. suites of ~300 tests) and **5 non-passing runs**.
- It caught **real product bugs**: 3 failed test(s) were reported with the failing test name and expected/actual values (see the failure taxonomy).
- It surfaced **Unity/project-level failure modes** distinct from test failures (build/import/bootstrap runs that produced no `results.xml` and never reached the test-execution phase).
- Every run left **inspectable artifacts** on disk (`summary.json`, `manifest.json`, `results.xml` when tests ran, `stdout.log`, `stderr.log`, `events.ndjson`).
- The artifacts let a reader **distinguish a test failure (exit 3, has results.xml) from an environment/import/bootstrap failure (exit 6, no results.xml)**.

## 5. Limitations

- This is **local dogfooding evidence by the tool's own author**, not independent third-party adoption or production usage.
- The archive contains machine-specific logs; absolute paths are sanitized in this report but the raw archive is left untouched.
- Some runs may be incomplete or malformed; such runs are reported honestly (incomplete/malformed runs: 0).
- This evidence primarily validates **`testplay-runner`**. It does **not** validate [`unity-ctx`](https://github.com/Kubonsang/unity-ctx) or [`unity-fileid-graph`](https://github.com/Kubonsang/unity-fileid-graph) — no logs for those tools are present in this archive.
- Long Unity startup/import times remain a performance concern: the longest observed run took 189s, and even passing runs spend a large fraction of time in the compile/import phase before tests execute.

## 6. Reproducibility

Regenerate this report and the machine-readable summary from the archive with:

```bash
python3 tools/analyze_testplay_dogfooding.py
```

The analyzer only reads the archive and is deterministic (no wall-clock timestamps in its output), so repeated runs produce identical files.

## 7. Public Safety

Generated reports sanitize local absolute paths: the source project root is shown as `<source-project-root>`, this repository as `<repo-root>`, and any remaining home-directory or volume absolute paths and the local username are redacted. The raw archive under `Other_Projects_testplay/` is preserved unmodified as the underlying evidence.

Small sanitized samples are provided under `docs/dogfooding/sanitized-samples/`:
- `docs/dogfooding/sanitized-samples/passing-run.summary.json`
- `docs/dogfooding/sanitized-samples/test-failure-run.md`
- `docs/dogfooding/sanitized-samples/bootstrap-failure-run.md`

## Appendix: per-run table

| Run | Status | Exit | Total | Pass | Fail | Skip | results.xml | Duration |
|---|---|---:|---:|---:|---:|---:|:--:|---:|
| `20260618-201430-99f28dfb` | pass | 0 | 284 | 283 | 0 | 1 | yes | 79s |
| `20260618-203804-df3f17cb` | pass | 0 | 280 | 279 | 0 | 1 | yes | 79s |
| `20260618-210424-aa0d68ff` | fail | 3 | 4 | 3 | 1 | 0 | yes | 84s |
| `20260618-210620-6f745900` | pass | 0 | 4 | 4 | 0 | 0 | yes | 86s |
| `20260618-210801-feae343f` | pass | 0 | 284 | 283 | 0 | 1 | yes | 85s |
| `20260618-211952-422015d9` | pass | 0 | 4 | 4 | 0 | 0 | yes | 84s |
| `20260618-212144-5a071b04` | pass | 0 | 284 | 283 | 0 | 1 | yes | 89s |
| `20260619-095826-b93c9d62` | pass | 0 | 4 | 4 | 0 | 0 | yes | 91s |
| `20260619-100025-0f97637d` | pass | 0 | 288 | 287 | 0 | 1 | yes | 75s |
| `20260619-100330-3e5f1857` | pass | 0 | 4 | 4 | 0 | 0 | yes | 70s |
| `20260619-100508-aa89ffa8` | pass | 0 | 288 | 287 | 0 | 1 | yes | 95s |
| `20260619-135142-486845ca` | pass | 0 | 11 | 11 | 0 | 0 | yes | 77s |
| `20260619-135323-e75da6c7` | pass | 0 | 299 | 298 | 0 | 1 | yes | 77s |
| `20260619-135532-d38902f6` | pass | 0 | 11 | 11 | 0 | 0 | yes | 82s |
| `20260619-135723-b456aefb` | pass | 0 | 299 | 298 | 0 | 1 | yes | 87s |
| `20260619-142754-a17758ee` | pass | 0 | 299 | 298 | 0 | 1 | yes | 74s |
| `20260621-193325-ed7d14b3` | fail | 6 | 0 | 0 | 0 | 0 | no | 189s |
| `20260621-193702-02ac0810` | fail | 6 | 0 | 0 | 0 | 0 | no | 189s |
| `20260621-200328-164b9ea2` | pass | 0 | 299 | 298 | 0 | 1 | yes | 90s |
| `20260622-002433-1a39a036` | pass | 0 | 4 | 4 | 0 | 0 | yes | 87s |
| `20260622-002659-ef669368` | pass | 0 | 303 | 302 | 0 | 1 | yes | 76s |
| `20260622-095321-807558c9` | pass | 0 | 5 | 5 | 0 | 0 | yes | 81s |
| `20260622-100533-d58b8049` | fail | 3 | 9 | 8 | 1 | 0 | yes | 92s |
| `20260622-101041-c1e2e241` | pass | 0 | 10 | 10 | 0 | 0 | yes | 73s |
| `20260622-101707-5f862646` | pass | 0 | 309 | 308 | 0 | 1 | yes | 81s |
| `20260622-110654-9008a51b` | pass | 0 | 311 | 310 | 0 | 1 | yes | 99s |
| `20260622-113125-bb7e79a9` | pass | 0 | 311 | 310 | 0 | 1 | yes | 97s |
| `20260622-114707-9754e1b6` | pass | 0 | 311 | 310 | 0 | 1 | yes | 89s |
| `20260622-135625-86016be8` | fail | 3 | 311 | 309 | 1 | 1 | yes | 90s |
| `20260622-135843-e7047451` | pass | 0 | 311 | 310 | 0 | 1 | yes | 81s |
