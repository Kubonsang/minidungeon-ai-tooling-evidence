# Sanitized sample — test assertion failure

- run id: `20260618-210424-aa0d68ff`
- exit code: 3
- totals: total=4 passed=3 failed=1 skipped=0

Failing test(s):
- `ResetVisualState_RestoresOriginalBaseColor` — ResetVisualState 후 MPB _BaseColor가 sharedMaterial의 원본 색으로 복원되어야 한다. Expected: RGBA(0.200, 0.700, 0.400, 1.000) But was: RGBA(0.200, 0.700, 0.400, 1.000)
