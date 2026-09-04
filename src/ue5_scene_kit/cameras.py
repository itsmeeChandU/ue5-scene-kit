"""CineCameraActor placement, lens validation, and common coverage patterns."""
from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Optional

from .errors import PropertyConformanceError, ValidationError
from .models import CameraSpec, LensSpec, Vec3
from .presets import LENSES
from .properties import read_property, set_and_verify
from .runtime import get_unreal


def _near(left: float, right: float) -> bool:
    return abs(float(left) - float(right)) <= 1e-4 * max(1.0, abs(float(right)))


def look_at_rotation(location_cm: Vec3, target_cm: Vec3) -> Vec3:
    """Calculate Unreal pitch/yaw/roll from a location toward a target."""
    dx = target_cm[0] - location_cm[0]
    dy = target_cm[1] - location_cm[1]
    dz = target_cm[2] - location_cm[2]
    planar = math.hypot(dx, dy)
    if planar == 0.0 and dz == 0.0:
        raise ValidationError("camera location and look-at target cannot be identical")
    pitch = math.degrees(math.atan2(dz, planar))
    yaw = math.degrees(math.atan2(dy, dx))
    return (pitch, yaw, 0.0)


def camera_spec(
    label: str,
    *,
    location_cm: Vec3,
    target_cm: Vec3,
    lens: str = "standard",
    focus_distance_cm: Optional[float] = None,
) -> CameraSpec:
    """Build a validated camera spec while deriving a true look-at rotation."""
    if lens not in LENSES:
        raise ValidationError(f"unknown lens {lens!r}; available: {sorted(LENSES)}")
    if focus_distance_cm is None:
        focus_distance_cm = math.dist(location_cm, target_cm)
    return CameraSpec(
        label=label,
        location_cm=location_cm,
        rotation_deg=look_at_rotation(location_cm, target_cm),
        lens=LENSES[lens],
        focus_distance_cm=focus_distance_cm,
    ).validate()


def spawn_camera(spec: CameraSpec):
    """Spawn a CineCameraActor and prove its lens/focus values landed."""
    spec.validate()
    ue = get_unreal()
    location = ue.Vector(*spec.location_cm)
    pitch, yaw, roll = spec.rotation_deg
    rotation = ue.Rotator(pitch=pitch, yaw=yaw, roll=roll)
    actor = ue.EditorLevelLibrary.spawn_actor_from_class(
        ue.CineCameraActor, location, rotation
    )
    if actor is None:
        raise RuntimeError(f"Unreal returned no CineCameraActor for {spec.label!r}")
    actor.set_actor_label(spec.label)
    component = actor.camera_component
    for name, asked in (
        ("current_focal_length", float(spec.lens.focal_length_mm)),
        ("current_aperture", float(spec.lens.aperture)),
    ):
        receipt = set_and_verify(component, name, asked, allow_clamp=True)
        if not _near(receipt["landed"], asked):
            raise PropertyConformanceError(
                f"camera {spec.label!r} asked for {name}={asked}, but the active "
                f"lens range clamped it to {receipt['landed']}. Widen lens_settings."
            )

    if spec.focus_distance_cm is not None:
        focus = read_property(component, "focus_settings")
        before = read_property(focus, "manual_focus_distance")
        set_and_verify(focus, "focus_method", ue.CameraFocusMethod.MANUAL)
        set_and_verify(focus, "manual_focus_distance", float(spec.focus_distance_cm))
        set_and_verify(component, "focus_settings", focus)
        committed = read_property(component, "focus_settings")
        landed = read_property(committed, "manual_focus_distance")
        method = read_property(committed, "focus_method")
        if method != ue.CameraFocusMethod.MANUAL:
            raise PropertyConformanceError("manual focus method did not survive struct write-back")
        if _near(landed, before) and not _near(before, spec.focus_distance_cm):
            raise PropertyConformanceError(
                "manual focus distance did not survive struct write-back"
            )
    return actor


def orbit_spec(
    label: str,
    target_cm: Vec3,
    *,
    radius_cm: float,
    azimuth_deg: float,
    height_cm: float = 0.0,
    lens: str = "standard",
) -> CameraSpec:
    """Place a camera on a horizontal orbit and point it at the target."""
    if radius_cm <= 0:
        raise ValidationError("radius_cm must be positive")
    angle = math.radians(azimuth_deg)
    location = (
        target_cm[0] + radius_cm * math.cos(angle),
        target_cm[1] + radius_cm * math.sin(angle),
        target_cm[2] + height_cm,
    )
    return camera_spec(label, location_cm=location, target_cm=target_cm, lens=lens)


def coverage_specs(
    prefix: str,
    target_cm: Vec3,
    *,
    radii_cm: Sequence[float] = (1500.0, 600.0, 200.0),
) -> tuple[CameraSpec, CameraSpec, CameraSpec]:
    """Return establishing, medium, and close coverage without spawning actors."""
    if len(radii_cm) != 3:
        raise ValidationError("radii_cm must contain wide, medium, and close radii")
    wide, medium, close = (float(value) for value in radii_cm)
    return (
        orbit_spec(f"{prefix}_Wide", target_cm, radius_cm=wide, azimuth_deg=-45,
                   height_cm=200, lens="wide"),
        orbit_spec(f"{prefix}_Medium", target_cm, radius_cm=medium, azimuth_deg=30,
                   height_cm=50, lens="standard"),
        orbit_spec(f"{prefix}_Close", target_cm, radius_cm=close, azimuth_deg=0,
                   height_cm=-50, lens="short_tele"),
    )


def spawn_coverage(
    prefix: str,
    target_cm: Vec3,
    *,
    radii_cm: Sequence[float] = (1500.0, 600.0, 200.0),
) -> list:
    """Spawn the three cameras produced by :func:`coverage_specs`."""
    return [spawn_camera(spec) for spec in coverage_specs(prefix, target_cm, radii_cm=radii_cm)]


def custom_lens(focal_length_mm: float, aperture: float) -> LensSpec:
    """Create and validate a lens outside the bundled preset table."""
    return LensSpec(float(focal_length_mm), float(aperture)).validate()
