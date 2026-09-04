"""Spawn Niagara systems as serialized level actors, not transient components."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Optional

from .errors import MissingAssetError, ValidationError
from .models import NiagaraSpec, Vec3
from .runtime import get_unreal


class NiagaraRegistry:
    """Intent-to-content-path registry with no bundled or assumed assets."""

    def __init__(self, paths: Optional[Mapping[str, str]] = None) -> None:
        self._paths: dict[str, str] = {}
        for intent, path in (paths or {}).items():
            self.register(intent, path)

    def register(self, intent: str, asset_path: str) -> None:
        intent = intent.strip()
        if not intent:
            raise ValidationError("Niagara intent cannot be blank")
        if not asset_path.startswith("/Game/"):
            raise ValidationError("Niagara content paths must start with /Game/")
        self._paths[intent] = asset_path

    def resolve(self, intent: str) -> str:
        try:
            return self._paths[intent]
        except KeyError as exc:
            raise ValidationError(
                f"unknown Niagara intent {intent!r}; registered: {sorted(self._paths)}"
            ) from exc

    def intents(self) -> list[str]:
        return sorted(self._paths)


def spawn_niagara(spec: NiagaraSpec):
    """Spawn a NiagaraActor that can survive an editor-to-render process boundary."""
    spec.validate()
    ue = get_unreal()
    system = ue.EditorAssetLibrary.load_asset(spec.asset_path)
    if system is None:
        raise MissingAssetError(f"Niagara system does not exist: {spec.asset_path}")
    pitch, yaw, roll = spec.rotation_deg
    actor = ue.EditorLevelLibrary.spawn_actor_from_class(
        ue.NiagaraActor,
        ue.Vector(*spec.location_cm),
        ue.Rotator(pitch=pitch, yaw=yaw, roll=roll),
    )
    if actor is None:
        raise RuntimeError(f"Unreal returned no NiagaraActor for {spec.asset_path}")
    actor.set_actor_label(spec.label)
    actor.set_actor_scale3d(ue.Vector(*spec.scale))
    actor.set_destroy_on_system_finish(spec.auto_destroy)
    component = actor.niagara_component
    if component is None:
        raise RuntimeError("NiagaraActor spawned without a NiagaraComponent")
    component.set_asset(system, False)
    return component


def spawn_intent(
    registry: NiagaraRegistry,
    intent: str,
    *,
    location_cm: Vec3,
    rotation_deg: Vec3 = (0.0, 0.0, 0.0),
    scale: Vec3 = (1.0, 1.0, 1.0),
    label: Optional[str] = None,
):
    """Resolve a project-owned asset path and spawn its persistent actor."""
    return spawn_niagara(
        NiagaraSpec(
            asset_path=registry.resolve(intent),
            label=label or intent,
            location_cm=location_cm,
            rotation_deg=rotation_deg,
            scale=scale,
        )
    )


def spawn_array(
    registry: NiagaraRegistry,
    intent: str,
    positions_cm: list[Vec3],
    *,
    scale: Vec3 = (1.0, 1.0, 1.0),
) -> list:
    """Spawn consistently named instances at several positions."""
    return [
        spawn_intent(
            registry,
            intent,
            location_cm=position,
            scale=scale,
            label=f"{intent}_{index:02d}",
        )
        for index, position in enumerate(positions_cm)
    ]
