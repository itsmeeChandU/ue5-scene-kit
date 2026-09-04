# Headless Linux

The public smoke fixture was verified with Unreal Engine
`5.4.4-35576357+UE5` on Linux, an NVIDIA RTX 3090, and Vulkan. This is the
tested boundary, not a claim that every container image or engine version
works.

## Container requirements

- a legally obtained Unreal Engine installation mounted or extracted at runtime
- an NVIDIA GPU exposed to the container
- NVIDIA user-space libraries matching the host driver
- a working Vulkan ICD and loader; validate them before launching Unreal
- a non-root runtime user with writable `HOME`, XDG config/data directories,
  project directory, and derived-data cache
- the Unreal project's Python Editor Script Plugin enabled

Do not bake or publish Epic's Unreal Engine binaries in a public image. A
portable image can contain the operating-system dependencies and this package,
then mount the user's licensed engine installation at runtime.

## Preflight

Before paying for engine startup, both commands should identify the assigned
NVIDIA GPU:

```bash
nvidia-smi
vulkaninfo --summary
```

If `nvidia-smi` succeeds but Vulkan selects software rendering or finds no
device, fix the container's NVIDIA user-space library/ICD setup first.

## Run the smoke fixture

From this repository, set paths appropriate to the container:

```bash
export SCENE_KIT_ROOT=/workspace/ue5-scene-kit
export SCENE_KIT_RECEIPT="$SCENE_KIT_ROOT/evidence/local-smoke-receipt.json"

/opt/UnrealEngine/Engine/Binaries/Linux/UnrealEditor \
  "$SCENE_KIT_ROOT/smoke/SceneKitSmoke.uproject" \
  -unattended -nopause -nosplash -RenderOffscreen \
  -SkipVulkanProfileCheck -NoVerifyGC \
  -stdout -FullStdOutLogOutput \
  -ExecutePythonScript="$SCENE_KIT_ROOT/smoke/run_smoke.py"
```

Success produces `SCENE_KIT_SMOKE_PASS` in the log and a JSON receipt. The
receipt is the result to retain; the full editor log can contain local paths
and environment details.

`-ExecutePythonScript` is suitable for the synchronous smoke script. The proof
capture registers an editor tick callback, so it must be started with
`-ExecCmds="py /absolute/path/to/smoke/render_proof.py"`; otherwise the editor
can exit before the asynchronous screenshot completes.
