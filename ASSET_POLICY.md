# Asset & Copyright Policy

This repository's **MiniDungeon demo** (`Assets/Demo/`) is a deliberately copyright-safe
test fixture. It exists to exercise an AI-agent Unity tooling stack, **not** as an art demo.

## Guarantees

- **No third-party assets.** Nothing in `Assets/Demo/` was obtained from another project,
  author, or library.
- **No Unity Asset Store assets.** No Asset Store package, sample, or content is used.
- **No downloaded models, textures, fonts, audio, or animations.** There are no `.fbx`,
  `.png`, `.jpg`, `.jpeg`, `.tga`, `.psd`, `.wav`, `.mp3`, `.ogg`, `.ttf`, `.otf`, `.blend`,
  or `.anim` files in the demo.
- **No AI-generated image/model/audio assets.**
- **Everything is reproducible from source.** All demo assets are built from:
  - Unity built-in primitive meshes (Cube, Sphere, Cylinder, Capsule), referenced by their
    built-in resource IDs — no mesh files are stored.
  - The built-in **Universal Render Pipeline/Lit** shader that ships with the project's
    installed `com.unity.render-pipelines.universal` package (a package shader, not a
    downloaded or third-party asset).
  - Generated materials (`.mat`), prefabs (`.prefab`), and a scene (`.unity`) authored by
    this repository's own generators.
  - C# scripts written in this repository.

## How the demo assets are produced

There are two equivalent, deterministic reproduction paths:

1. **In Unity (Editor):** menu `Tools/Demo/Regenerate MiniDungeon Demo`
   (`Assets/Demo/Editor/DemoAssetGenerator.cs`).
2. **Offline (no Unity):** `python3 tools/generate_yaml_fixtures.py`, which writes the
   serialized Unity YAML files and their `.meta` files directly.

Both paths use only the sources listed above. GUIDs are derived deterministically, so
regeneration is idempotent.

## Purpose

This demo is a copyright-safe test fixture for:

- [testplay-runner](https://github.com/Kubonsang/testplay-runner) — compile checks and
  EditMode/PlayMode test execution.
- [unity-ctx](https://github.com/Kubonsang/unity-ctx) — scene/prefab structure inspection
  and safe property mutation.
- [unity-fileid-graph](https://github.com/Kubonsang/unity-fileid-graph) — fileID/reference
  graph validation.
