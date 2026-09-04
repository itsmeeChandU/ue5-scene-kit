"""Persistent WindDirectionalSource helpers."""
from __future__ import annotations

from .errors import ValidationError
from .presets import WINDS
from .properties import set_and_verify
from .runtime import get_unreal


def spawn_wind(preset: str = "breeze", *, yaw_deg: float = 0.0, label: str = "WindSource"):
    if preset not in WINDS:
        raise ValidationError(f"unknown wind {preset!r}; available: {sorted(WINDS)}")
    spec = WINDS[preset].validate()
    ue = get_unreal()
    actor = ue.EditorLevelLibrary.spawn_actor_from_class(
        ue.WindDirectionalSource,
        ue.Vector(0.0, 0.0, 500.0),
        ue.Rotator(pitch=0.0, yaw=float(yaw_deg), roll=0.0),
    )
    if actor is None or actor.component is None:
        raise RuntimeError("WindDirectionalSource did not expose a component")
    actor.set_actor_label(label)
    set_and_verify(actor.component, "strength", spec.strength, allow_clamp=True)
    set_and_verify(actor.component, "speed", spec.speed, allow_clamp=True)
    set_and_verify(actor.component, "min_gust_amount", spec.minimum_gust, allow_clamp=True)
    return actor
