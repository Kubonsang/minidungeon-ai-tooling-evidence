# MiniDungeon Demo Fixture

A minimal, **copyright-safe** Unity demo used to prove an AI-agent Unity tooling pipeline:

1. [`unity-ctx`](https://github.com/Kubonsang/unity-ctx) inspects scene/prefab structure.
2. [`unity-fileid-graph`](https://github.com/Kubonsang/unity-fileid-graph) validates the
   fileID/reference graph.
3. [`testplay-runner`](https://github.com/Kubonsang/testplay-runner) runs compile checks and
   EditMode/PlayMode tests.
4. An AI coding agent safely modifies simple scene/prefab properties and verifies the result.

> This is **not** an art demo. It is a test fixture for AI-agent Unity orchestration.
> See [`/ASSET_POLICY.md`](../../ASSET_POLICY.md). No external assets are used.

Unity version: **6000.3.8f1** (URP). Only built-in primitives, the built-in URP/Lit shader,
generated materials, and the C# scripts in this folder are used.

## Layout

```
Assets/Demo/
  Scenes/MiniDungeon.unity        Start room + combat room + door + 4 torches +
                                  immortal dummy + player spawn + room-state controller
  Prefabs/
    Room_Start.prefab             Root + Floor_Cube
    Room_Combat.prefab            Root + Floor_Cube
    Door.prefab                   Door(DemoDoor) > Frame_Left, Frame_Right, DoorPanel
    Torch.prefab                  Torch(DemoTorch) > Base_Cylinder, Flame_Sphere, Light_Point
    DummyTarget.prefab            DummyTarget(DemoDummyTarget) > Body_Capsule, Head_Sphere, Hitbox
    PlayerSpawn.prefab            Empty marker (Transform only)
  Materials/                      M_Stone, M_Wood, M_Torch_On, M_Torch_Off, M_Dummy, M_Door (URP/Lit)
  Scripts/                        DemoTorch, DemoDoor, DemoRoomState, DemoDummyTarget, DemoBootstrap
  Editor/DemoAssetGenerator.cs    Tools/Demo/Regenerate MiniDungeon Demo
  Tests/EditMode/                 DemoAssetIntegrityTests
  Tests/PlayMode/                 MiniDungeonPlayModeTests
```

Scene objects use **unique, deterministic names** (`Torch_01`..`Torch_04`,
`RoomStateController`, `DummyTarget`, `Door`, `PlayerSpawn`) so CLI tools can target them by
name without ambiguity.

## Regenerate the demo

Two equivalent, deterministic, idempotent paths:

- **In Unity:** menu **`Tools/Demo/Regenerate MiniDungeon Demo`**
- **Offline (no Unity):** `python3 tools/generate_yaml_fixtures.py` (run from the project root)

## Inspect with unity-ctx

```bash
unity-ctx scene summarize Assets/Demo/Scenes/MiniDungeon.unity
# OK SCENE ... game_objects=30 components=77 unknown=0

unity-ctx scene query Assets/Demo/Scenes/MiniDungeon.unity --name Torch_01
# FOUND fileID=127 type=GameObject name="Torch_01"

unity-ctx scene query Assets/Demo/Scenes/MiniDungeon.unity --type MonoBehaviour
# 8 matches: 4x DemoTorch, DemoDoor, DemoDummyTarget, DemoRoomState, DemoBootstrap

# Read a field (--id is the GameObject fileID; Torch_01 = 127):
unity-ctx scene get Assets/Demo/Scenes/MiniDungeon.unity --id 127 --component MonoBehaviour --field startLit
# OK field=startLit value=0

unity-ctx prefab refs   Assets/Demo/Prefabs/Torch.prefab
unity-ctx prefab deps   Assets/Demo/Prefabs/Torch.prefab --project .
```

### Modify a property (dry-run by default, add `--write --ack-impact` to commit)

```bash
unity-ctx prefab set Assets/Demo/Prefabs/Torch.prefab --project . --id 600002 --field startLit  --value 1
unity-ctx prefab set Assets/Demo/Prefabs/Door.prefab  --project . --id 600002 --field startOpen --value 1
# DRY_RUN field=startLit old=0 new=1 ... changed=1 impact_status=OK
```

## Validate the fileID graph with unity-fileid-graph (`uyaml`)

```bash
uyaml prefab check Assets/Demo/Prefabs/Torch.prefab
uyaml scene  check Assets/Demo/Scenes/MiniDungeon.unity --json
# GRAPH_CHECK status=WARN ... (exit 0). No ERROR codes = graph is valid.
```

> **About the WARN lines.** `uyaml`/`unity-ctx` only model `GameObject` and `Transform`.
> `UNKNOWN_CLASS_ID` (for MeshRenderer/MeshFilter/Light/BoxCollider/scene settings) and
> `UNKNOWN_FIELD_SHAPE` (`unsupported Transform.m_Children shape`) are **warning-only**,
> exit code 0, and `errors=0`. These same warnings appear on genuine Unity-authored files;
> they do not indicate a problem with this fixture.

## Run the tests with testplay-runner

The committed `testplay.json` / `testplay.playmode.json` are portable — they omit the
machine-specific Unity path and project path. Point `testplay` at your Unity 6000.3.8f1 editor
binary via the `UNITY_PATH` environment variable (or `--unity-path`):

```bash
export UNITY_PATH="…/Unity"   # your Unity 6000.3.8f1 editor binary (e.g. from Unity Hub)
testplay check          # validate Unity path, project path, testplay.json
testplay list           # static scan of test names
testplay run            # compile + run EditMode tests (testplay.json)
testplay run --config testplay.playmode.json   # PlayMode tests
```

Tests verify: the scene loads, exactly four torches exist, the dummy target exists and is
immortal (survives many hits, never destroyed), the start room completes when all torches are
lit, no required prefab reference / script is missing, and the runtime scripts compile with no
external-package dependencies.

## Reproducible demo runners

Two scripts run the documented commands in order, capture per-step `stdout`/`stderr`, and write a
portfolio-safe `report.md` (absolute paths shown as `<repo-root>`). All outputs go to
`artifacts/demo-e2e/`. Each runner exits non-zero if any step fails.

```bash
# Fast: no Unity required, runs in ~1s
python3 tools/run_demo_fast.py
#   1) unity-ctx scene summarize
#   2) unity-ctx prefab set startLit (dry-run)   # dry-run: does not modify the prefab
#   3) uyaml scene check --json

# Full end-to-end: the three fast checks plus the real Unity test suites (several minutes)
python3 tools/run_demo_e2e.py
#   4) testplay run --filter DemoDungeon                                   # EditMode
#   5) testplay run --config testplay.playmode.json --filter DemoDungeon   # PlayMode
```

**Pass criteria**

| Step | Passes when |
|------|-------------|
| `unity-ctx scene summarize` / `prefab set` | process exit code `0` |
| `uyaml scene check --json` | process exit code `0` **and** `summary.errors == 0` (warnings are non-fatal) |
| `testplay run` (EditMode / PlayMode) | process exit code `0` (`failed == 0`) |
| Overall runner | every step above passes |

The report includes a dedicated **uyaml warning summary** counting warnings by code
(`UNKNOWN_CLASS_ID`, etc.) and restating that exit `0` + `errors=0` are the pass criteria.
Those `UNKNOWN_*` warnings are expected (uyaml models only GameObject/Transform) and also occur
on genuine Unity files.

### Optional: actual-apply test

`tools/run_demo_apply_e2e.py` is a stronger, **write-path** variant. Instead of a dry-run it
applies a real property change and proves it is fully reversible:

```bash
python3 tools/run_demo_apply_e2e.py   # writes to the repo, then restores the baseline
```

1. Regenerate the fixture to a baseline (offline generator) and snapshot it.
2. `unity-ctx prefab set … startLit 1 --write --ack-impact` (real on-disk write; creates a `.bak`).
3. `uyaml prefab check --json` on the mutated prefab (must stay `errors=0`).
4. `testplay run` EditMode and PlayMode.
5. Regenerate to restore the baseline and delete the `.bak`.
6. Confirm the working tree is clean — `git status --porcelain -- Assets/Demo` when in a git
   repo, otherwise a sha256 content comparison vs the baseline — or report the changed files.

Output goes to `artifacts/demo-e2e/apply/report.md`. It exits non-zero if any step fails **or**
the fixture is not byte-identical to the baseline afterwards.

## Note for macOS + exFAT/FAT volumes

On such volumes macOS may create hidden `._*` AppleDouble files next to each asset. Unity
ignores them, but CLI tools that scan the project can choke on them. Remove with:

```bash
xattr -rc Assets ; find Assets -name '._*' -delete    # or: dot_clean .
```
