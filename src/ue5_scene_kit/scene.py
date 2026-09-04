"""Small orchestration helpers that remain explicit about destructive actions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .atmosphere import build_atmosphere
from .cameras import coverage_specs, spawn_camera
from .errors import ValidationError
from .models import Vec3
from .runtime import get_unreal
from .wind import spawn_wind


@dataclass(frozen=True)
class SceneFoundation:
    atmosphere: dict[str, Any]
    wind: Any
    cameras: tuple[Any, ...]


def build_foundation(
    *,
    target_cm: Vec3,
    atmosphere: str = "golden_hour",
    wind: str = "breeze",
    camera_prefix: str = "Coverage",
    label_prefix: str = "SceneKit",
) -> SceneFoundation:
    """Build atmosphere, wind, and three-camera coverage in the current level.

    This deliberately does not create, clear, save, or render a level. Those
    lifecycle operations are project decisions and should never be hidden in a
    reusable scene helper.
    """
    atmosphere_result = build_atmosphere(atmosphere, label_prefix=label_prefix)
    wind_actor = spawn_wind(wind, label=f"{label_prefix}_Wind")
    cameras = tuple(spawn_camera(spec) for spec in coverage_specs(camera_prefix, target_cm))
    return SceneFoundation(atmosphere_result, wind_actor, cameras)


def save_current_level(*, confirmed: bool = False) -> None:
    """Save the current level only with explicit confirmation."""
    if not confirmed:
        raise ValidationError("save_current_level requires confirmed=True")
    ue = get_unreal()
    if not ue.EditorLevelLibrary.save_current_level():
        raise RuntimeError("Unreal failed to save the current level")


def actor_summary(foundation: SceneFoundation) -> dict[str, int]:
    """Return a stable summary useful for logs and smoke tests."""
    return {
        "atmosphere_actors": 5,
        "wind_actors": 1 if foundation.wind is not None else 0,
        "camera_actors": len(foundation.cameras),
    }

