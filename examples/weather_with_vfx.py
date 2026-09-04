"""Project-owned Niagara paths are registered by intent, never bundled here."""
from ue5_scene_kit.niagara import NiagaraRegistry
from ue5_scene_kit.weather import build_weather

registry = NiagaraRegistry({"rain": "/Game/MyProject/VFX/NS_Rain"})
result = build_weather("rain_light", vfx_registry=registry)

print(result["weather"])

