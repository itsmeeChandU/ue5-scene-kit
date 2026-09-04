# Live-engine smoke test

This fixture validates the package inside a clean Unreal Editor project. It
creates a new map, builds the scene foundation, validates camera lenses and
focus, composes a weather preset, saves the map, and writes
`smoke-receipt.json`.

```bash
SCENE_KIT_ROOT=/absolute/path/to/ue5-scene-kit \
SCENE_KIT_RECEIPT=/absolute/path/to/smoke-receipt.json \
/path/to/UnrealEditor smoke/SceneKitSmoke.uproject \
  -unattended -nopause -nosplash -stdout -FullStdOutLogOutput \
  -ExecutePythonScript=/absolute/path/to/smoke/run_smoke.py
```

The test does not require project assets, render frames, or network access.
It modifies only the disposable `SceneKitSmoke` project.

`render_proof.py` is a separate visual check. It builds a small composition
from Unreal's built-in cube, cylinder, and sphere meshes, applies repository-
generated materials, pilots the package's wide camera, and captures a PNG from
the live editor viewport. No Marketplace, Fab, or private project assets are
used.
