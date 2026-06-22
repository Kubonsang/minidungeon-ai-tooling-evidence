# MiniDungeon E2E Demo Report (full)

- Generated: 2026-06-22T05:38:46Z
- Mode: full
- Project root: `<repo-root>`
- Pre-step: removed 0 macOS `._*` AppleDouble file(s)
- **Overall: PASS (5/5 steps passed)**

| # | Step | Status | Exit | Duration | Result |
|---|------|--------|------|----------|--------|
| 1 | unity-ctx scene summarize | PASS | 0 | 0.0s | OK SCENE file=Assets/Demo/Scenes/MiniDungeon.unity game_objects=30 components=77 unknown=0 |
| 2 | unity-ctx prefab set startLit (dry-run) | PASS | 0 | 0.0s | DRY_RUN field=startLit old=0 new=1 type_hint=int changed=1 impact_status=OK scenes=0 scene_refs=0 prefabs=0 prefab_refs=0 nested_depth=0 ack_required=1 pre_check=WARN temp_check=WARN |
| 3 | uyaml scene check (--json) | PASS | 0 | 0.0s | status=WARN errors=0 warnings=38 |
| 4 | testplay run (EditMode) | PASS | 0 | 218.5s | total=11 passed=11 failed=0 |
| 5 | testplay run (PlayMode) | PASS | 0 | 212.3s | total=4 passed=4 failed=0 |

## uyaml scene check — warning summary

Pass criteria: **process exit code 0 AND `summary.errors == 0`**. Warnings are non-fatal.

- exit code: 0 (pass)
- status: WARN
- errors: 0 (pass)
- warnings: 38 (non-fatal)
- warning types:
  - `UNKNOWN_CLASS_ID`: 38

> These `UNKNOWN_*` warnings are emitted because uyaml models only GameObject and Transform (MeshRenderer / MeshFilter / Light / BoxCollider / MonoBehaviour / scene-settings blocks are skipped). They also appear on genuine Unity files and do not indicate a defect.

## Step details

### 1. unity-ctx scene summarize — PASS

- Command: `unity-ctx scene summarize Assets/Demo/Scenes/MiniDungeon.unity`
- Exit code: 0
- Duration: 0.0s
- Result: OK SCENE file=Assets/Demo/Scenes/MiniDungeon.unity game_objects=30 components=77 unknown=0
- stdout: `artifacts/demo-e2e/01_unity-ctx-scene-summarize.stdout.log`
- stderr: `artifacts/demo-e2e/01_unity-ctx-scene-summarize.stderr.log`

### 2. unity-ctx prefab set startLit (dry-run) — PASS

- Command: `unity-ctx prefab set Assets/Demo/Prefabs/Torch.prefab --project . --id 600002 --field startLit --value 1`
- Exit code: 0
- Duration: 0.0s
- Result: DRY_RUN field=startLit old=0 new=1 type_hint=int changed=1 impact_status=OK scenes=0 scene_refs=0 prefabs=0 prefab_refs=0 nested_depth=0 ack_required=1 pre_check=WARN temp_check=WARN
- stdout: `artifacts/demo-e2e/02_unity-ctx-prefab-set.stdout.log`
- stderr: `artifacts/demo-e2e/02_unity-ctx-prefab-set.stderr.log`

### 3. uyaml scene check (--json) — PASS

- Command: `uyaml scene check Assets/Demo/Scenes/MiniDungeon.unity --json`
- Exit code: 0
- Duration: 0.0s
- Result: status=WARN errors=0 warnings=38
- Note: exit 0 and errors=0 (warnings non-fatal)
- stdout: `artifacts/demo-e2e/03_uyaml-scene-check.stdout.log`
- stderr: `artifacts/demo-e2e/03_uyaml-scene-check.stderr.log`

### 4. testplay run (EditMode) — PASS

- Command: `testplay run --filter DemoDungeon`
- Exit code: 0
- Duration: 218.5s
- Result: total=11 passed=11 failed=0
- stdout: `artifacts/demo-e2e/04_testplay-editmode.stdout.log`
- stderr: `artifacts/demo-e2e/04_testplay-editmode.stderr.log`

### 5. testplay run (PlayMode) — PASS

- Command: `testplay run --config testplay.playmode.json --filter DemoDungeon`
- Exit code: 0
- Duration: 212.3s
- Result: total=4 passed=4 failed=0
- stdout: `artifacts/demo-e2e/05_testplay-playmode.stdout.log`
- stderr: `artifacts/demo-e2e/05_testplay-playmode.stderr.log`
