"""Composition layer for atmosphere, wind, and optional project-owned VFX."""
from __future__ import annotations

from typing import Any, Optional

from .atmosphere import build_atmosphere
from .errors import ValidationError
from .models import NiagaraSpec
from .niagara import NiagaraRegistry, spawn_niagara
from .presets import WEATHER
from .wind import spawn_wind


def build_weather(
    weather: str = "golden_clear",
    *,
    vfx_registry: Optional[NiagaraRegistry] = None,
    vfx_location_cm: tuple[float, float, float] = (0.0, 0.0, 4000.0),
    vfx_scale: tuple[float, float, float] = (50.0, 50.0, 50.0),
    label_prefix: str = "SceneKit",
) -> dict[str, Any]:
    """Build named weather without silently inventing missing VFX assets.

    If the preset calls for rain, snow, or dust, a registry containing that
    intent is mandatory. This avoids publishing fake `/Game/...` paths.
    """
    if weather not in WEATHER:
        raise ValidationError(f"unknown weather {weather!r}; available: {sorted(WEATHER)}")
    atmosphere_name, overrides, wind_name, vfx_intent = WEATHER[weather]
    vfx_asset_path = None
    if vfx_intent is not None:
        if vfx_registry is None:
            raise ValidationError(
                f"weather {weather!r} requires a project-owned Niagara intent "
                f"{vfx_intent!r}; pass a NiagaraRegistry"
            )
        vfx_asset_path = vfx_registry.resolve(vfx_intent)
    atmosphere = build_atmosphere(
        atmosphere_name, overrides=overrides, label_prefix=label_prefix
    )
    wind = spawn_wind(wind_name, label=f"{label_prefix}_Wind_{weather}")
    vfx = None
    if vfx_intent is not None:
        assert vfx_asset_path is not None
        vfx = spawn_niagara(
            NiagaraSpec(
                asset_path=vfx_asset_path,
                label=f"{label_prefix}_VFX_{weather}",
                location_cm=vfx_location_cm,
                scale=vfx_scale,
            )
        )
    return {
        "weather": weather,
        "atmosphere": atmosphere,
        "wind": wind,
        "vfx": vfx,
    }
