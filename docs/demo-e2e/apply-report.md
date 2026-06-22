# MiniDungeon ACTUAL-APPLY E2E Report

- Generated: 2026-06-22T02:45:00Z
- Project root: `<repo-root>`
- Mutation: `Assets/Demo/Prefabs/Torch.prefab` field `startLit` 0 -> 1 (real --write --ack-impact), then restored
- **Overall: PASS (7/7 checks passed)**

| # | Step | Status | Exit | Duration | Result |
|---|------|--------|------|----------|--------|
| 1 | Regenerate baseline (offline generator) | PASS | 0 | 0.1s | Generated 48 files: |
| 2 | Apply unity-ctx prefab set startLit=1 (--write --ack-impact) | PASS | 0 | 0.0s | WRITE backup=Assets/Demo/Prefabs/Torch.prefab.bak field=startLit old=0 new=1 type_hint=int changed=1 verified=1 impact_status=OK scenes=0 scene_refs=0 prefabs=0 prefab_refs=0 nested_depth=0 pre_check=WARN temp_check=WARN final_check=WARN |
| 3 | uyaml prefab check (mutated, --json) | PASS | 0 | 0.0s | status=WARN errors=0 warnings=5 |
| 4 | testplay run (EditMode) | PASS | 0 | 208.8s | total=11 passed=11 failed=0 |
| 5 | testplay run (PlayMode) | PASS | 0 | 210.3s | total=4 passed=4 failed=0 |
| 6 | Regenerate to restore baseline | PASS | 0 | 0.3s | Generated 48 files: |
| 7 | Working tree clean (fixture restored) | PASS | - | - | clean (60 files match baseline) |

## uyaml prefab check — warning summary

Pass criteria: **process exit code 0 AND `summary.errors == 0`**. Warnings are non-fatal.

- exit code: 0 (pass)
- status: WARN
- errors: 0 (pass)
- warnings: 5 (non-fatal)
- warning types:
  - `UNKNOWN_CLASS_ID`: 5

## Working tree cleanliness

Mechanism: content-hash (sha256) comparison vs baseline (not a git repository)

- removed tool-created backups: `Assets/Demo/Prefabs/Torch.prefab.bak`
- Result: **clean** — fixture is byte-identical to the regenerated baseline.

## Step details

### 1. Regenerate baseline (offline generator) — PASS

- Command: `python3 tools/generate_yaml_fixtures.py`
- Exit code: 0
- Duration: 0.1s
- Result: Generated 48 files:
- stdout: `artifacts/demo-e2e/apply/01_regenerate-baseline.stdout.log`
- stderr: `artifacts/demo-e2e/apply/01_regenerate-baseline.stderr.log`

### 2. Apply unity-ctx prefab set startLit=1 (--write --ack-impact) — PASS

- Command: `unity-ctx prefab set Assets/Demo/Prefabs/Torch.prefab --project . --id 600002 --field startLit --value 1 --write --ack-impact`
- Exit code: 0
- Duration: 0.0s
- Result: WRITE backup=Assets/Demo/Prefabs/Torch.prefab.bak field=startLit old=0 new=1 type_hint=int changed=1 verified=1 impact_status=OK scenes=0 scene_refs=0 prefabs=0 prefab_refs=0 nested_depth=0 pre_check=WARN temp_check=WARN final_check=WARN
- Note: write committed and re-validated (.bak backup created)
- stdout: `artifacts/demo-e2e/apply/02_unity-ctx-prefab-set-write.stdout.log`
- stderr: `artifacts/demo-e2e/apply/02_unity-ctx-prefab-set-write.stderr.log`

### 3. uyaml prefab check (mutated, --json) — PASS

- Command: `uyaml prefab check Assets/Demo/Prefabs/Torch.prefab --json`
- Exit code: 0
- Duration: 0.0s
- Result: status=WARN errors=0 warnings=5
- Note: exit 0 and errors=0 (warnings non-fatal)
- stdout: `artifacts/demo-e2e/apply/03_uyaml-prefab-check.stdout.log`
- stderr: `artifacts/demo-e2e/apply/03_uyaml-prefab-check.stderr.log`

### 4. testplay run (EditMode) — PASS

- Command: `testplay run --filter DemoDungeon`
- Exit code: 0
- Duration: 208.8s
- Result: total=11 passed=11 failed=0
- stdout: `artifacts/demo-e2e/apply/04_testplay-editmode.stdout.log`
- stderr: `artifacts/demo-e2e/apply/04_testplay-editmode.stderr.log`

### 5. testplay run (PlayMode) — PASS

- Command: `testplay run --config testplay.playmode.json --filter DemoDungeon`
- Exit code: 0
- Duration: 210.3s
- Result: total=4 passed=4 failed=0
- stdout: `artifacts/demo-e2e/apply/05_testplay-playmode.stdout.log`
- stderr: `artifacts/demo-e2e/apply/05_testplay-playmode.stderr.log`

### 6. Regenerate to restore baseline — PASS

- Command: `python3 tools/generate_yaml_fixtures.py`
- Exit code: 0
- Duration: 0.3s
- Result: Generated 48 files:
- stdout: `artifacts/demo-e2e/apply/06_regenerate-restore.stdout.log`
- stderr: `artifacts/demo-e2e/apply/06_regenerate-restore.stderr.log`
