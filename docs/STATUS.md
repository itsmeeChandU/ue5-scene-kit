# Scope and status

Current release: `0.1.0-alpha`

## What is verified offline

- imports without Unreal installed
- all bundled specs validate
- unknown fields and invalid numeric values fail explicitly
- property writes distinguish conformance, clamps, inert values, and missing names
- camera look-at and coverage math
- actor-adapter call shapes against a deterministic fake Unreal API
- wheel/sdist construction on ordinary CPython

## What still needs live-engine evidence

- a public compatibility matrix across supported Unreal Engine versions
- screenshots or level artifacts produced by this standalone repository
- a repeatable plugin/path installation recipe for Windows and Linux editors
- render-level proof that each preset creates a materially distinct image

Offline tests prove the package's Python behavior but are not presented as an
Unreal Engine compatibility guarantee.

## Deliberately excluded from v0.1

- custom C++ modules
- Unreal Engine source or binaries
- Fab, Megascans, Marketplace, or project content assets
- hard-coded project maps and content paths
- level deletion or automatic map overwrites
- Movie Render Queue dispatch (use UE5 MRQ Guard)
- unfinished character, landscape, foliage, material-graph, and Sequencer APIs

These exclusions keep the first release focused, portable, and independently
useful.
