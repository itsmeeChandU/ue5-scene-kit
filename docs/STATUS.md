# Scope and status

Current release: `0.2.0-alpha`

## What is verified offline

- imports without Unreal installed
- all bundled specs validate
- unknown fields and invalid numeric values fail explicitly
- property writes distinguish conformance, clamps, inert values, and missing names
- camera look-at and coverage math
- actor-adapter call shapes against a deterministic fake Unreal API
- idempotent project installation and explicit safe replacement
- wheel/sdist construction on ordinary CPython

## What is verified in a live engine

- Unreal Engine `5.4.4-35576357+UE5` on Linux
- NVIDIA RTX 3090 through Vulkan
- atmosphere foundation and wide/medium/close camera creation
- weather-preset composition without invented VFX assets
- explicit save producing a non-empty `.umap`
- 1920x1080 proof capture using built-in meshes and repository-authored materials

See the [receipt](../evidence/ue5.4.4-smoke-receipt.json),
[proof image](../evidence/ue5.4.4-proof.png), and
[smoke fixture](../smoke/README.md).

## What still needs live-engine evidence

- a public compatibility matrix beyond Unreal Engine 5.4.4 on Linux
- direct editor-path smoke runs on Windows and macOS
- render-level proof that each preset creates a materially distinct image

Offline tests prove the package's Python behavior but are not presented as an
Unreal Engine compatibility guarantee.

## Deliberately excluded

- custom C++ modules
- Unreal Engine source or binaries
- Fab, Megascans, Marketplace, or project content assets
- hard-coded project maps and content paths
- level deletion or automatic map overwrites
- Movie Render Queue dispatch (use UE5 MRQ Guard)
- unfinished character, landscape, foliage, material-graph, and Sequencer APIs

These exclusions keep the first release focused, portable, and independently
useful.
