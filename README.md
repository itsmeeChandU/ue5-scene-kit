<p align="center">
  <img src="assets/logo.png" width="180" alt="UE5 Scene Kit logo">
</p>

# UE5 Scene Kit

Fail-loud Unreal Engine editor-Python primitives for building cinematic scene
foundations: cameras, atmosphere, fog, wind, weather, and persistent Niagara
actors.

<p align="center">
  <img src="assets/banner.png" alt="Cinematic scene primitives assembling into a landscape">
</p>

[![CI](https://github.com/itsmeeChandU/ue5-scene-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/itsmeeChandU/ue5-scene-kit/actions/workflows/ci.yml)
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL%202.0-blue.svg)](LICENSE)
[![Status: alpha](https://img.shields.io/badge/status-alpha-f4b942.svg)](docs/STATUS.md)

## Why this exists

Unreal scene automation often looks successful while producing the wrong
scene: a property name is invalid, a value is clamped, a struct mutation is
never written back, an effect is transient, or a helper saves a map when the
caller did not intend it. This package makes those decisions explicit.

It is not an asset pack, renderer, movie generator, or replacement for Unreal.
It is a small source library intended to run inside Unreal Editor's embedded
Python.

## Included in v0.1

- strict editor-property writes with before/asked/landed receipts
- immutable, offline-validatable lens, atmosphere, wind, and Niagara specs
- true look-at rotations plus wide/medium/close camera coverage
- sun + SkyAtmosphere + SkyLight + height fog + unbound post-process foundation
- persistent `NiagaraActor` spawning from project-supplied `/Game/...` paths
- wind and weather composition without bundled or invented VFX assets
- explicit opt-in level saving
- ordinary-Python tests using an Unreal-compatible fake runtime

Landscape import, foliage painting, material graph authoring, Sequencer, and
MRQ orchestration are intentionally outside this first release. See
[scope and status](docs/STATUS.md).

## Install for development

```bash
git clone https://github.com/itsmeeChandU/ue5-scene-kit.git
cd ue5-scene-kit
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest
```

The package has no runtime dependency on PyPI's unrelated `unreal` package.
Actual actor construction must run under Unreal Editor, where Epic supplies
the `unreal` module.

## Use inside Unreal Editor

Make this repository's `src` directory importable by Unreal's Python
environment, then run a script like:

```python
from ue5_scene_kit import build_foundation

foundation = build_foundation(
    target_cm=(0.0, 0.0, 100.0),
    atmosphere="golden_hour",
    wind="breeze",
    camera_prefix="Subject",
)

print(len(foundation.cameras))  # 3
```

The call creates actors in the current level but does not save it. Saving is
separate and deliberately explicit:

```python
from ue5_scene_kit import save_current_level

save_current_level(confirmed=True)
```

For headless/editor-command execution:

```bash
UnrealEditor-Cmd /path/to/Project.uproject \
  -unattended -nosplash -stdout -FullStdOutLogOutput \
  -ExecutePythonScript=/absolute/path/to/examples/build_scene.py
```

Executable paths and command-line flags vary by platform and engine install.
This library does not redistribute Unreal Engine.

## Project-owned Niagara assets

No VFX assets are bundled, and no fake content paths are assumed:

```python
from ue5_scene_kit.niagara import NiagaraRegistry
from ue5_scene_kit.weather import build_weather

registry = NiagaraRegistry({
    "rain": "/Game/MyProject/VFX/NS_Rain",
})
result = build_weather("rain_light", vfx_registry=registry)
```

If the asset does not exist, `MissingAssetError` is raised before the scene is
treated as built.

## Property safety

```python
from ue5_scene_kit import set_and_verify

receipt = set_and_verify(component, "fog_density", 0.08)
print(receipt["before"], receipt["asked"], receipt["landed"])
```

A missing property, discarded write, unexpected clamp, or lost read-back is a
typed exception. `allow_clamp=True` is available only when the caller has
deliberately accepted an engine clamp; the returned `landed` value remains the
source of truth.

## Verification boundary

CI validates the pure-Python models, adapters against a fake Unreal surface,
lint, and package builds on Python 3.9 and 3.12. This v0.1 package has not yet
completed a public live-engine compatibility matrix. It is alpha, and that
boundary is intentional rather than hidden.

## License and trademark

Source and repository-owned visual assets are available under the
[Mozilla Public License 2.0](LICENSE). Unreal Engine is proprietary software
from Epic Games and is not included. “Unreal”, “Unreal Engine”, and their
marks belong to Epic Games. This independent community project is not
affiliated with or endorsed by Epic Games.

## Relationship to MRQ Guard

[UE5 MRQ Guard](https://github.com/itsmeeChandU/ue5-mrq-guard) handles the
render boundary: process roles, cost limits, artifact checks, cloud staging,
and output verification. UE5 Scene Kit handles scene construction. Each
package can be used independently.
