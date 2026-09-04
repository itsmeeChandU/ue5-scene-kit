"""Validated, serializable specifications used by the Unreal adapters."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from typing import Any, Optional

from .errors import ValidationError

Vec3 = tuple[float, float, float]
Color = tuple[float, float, float, float]


def _finite(name: str, value: float) -> float:
    value = float(value)
    if value != value or value in (float("inf"), float("-inf")):
        raise ValidationError(f"{name} must be finite, got {value!r}")
    return value


def _positive(name: str, value: float, *, allow_zero: bool = False) -> float:
    value = _finite(name, value)
    if value < 0 if allow_zero else value <= 0:
        relation = "non-negative" if allow_zero else "positive"
        raise ValidationError(f"{name} must be {relation}, got {value}")
    return value


def _vec3(name: str, value: Vec3) -> Vec3:
    if len(value) != 3:
        raise ValidationError(f"{name} must contain exactly 3 numbers")
    return tuple(_finite(f"{name}[{index}]", part) for index, part in enumerate(value))  # type: ignore[return-value]


def _color(name: str, value: Color) -> Color:
    if len(value) != 4:
        raise ValidationError(f"{name} must contain RGBA values")
    result = tuple(_finite(f"{name}[{index}]", part) for index, part in enumerate(value))
    if any(part < 0 for part in result):
        raise ValidationError(f"{name} cannot contain negative channels")
    return result  # type: ignore[return-value]


@dataclass(frozen=True)
class LensSpec:
    focal_length_mm: float
    aperture: float

    def validate(self) -> LensSpec:
        _positive("focal_length_mm", self.focal_length_mm)
        _positive("aperture", self.aperture)
        return self


@dataclass(frozen=True)
class CameraSpec:
    label: str
    location_cm: Vec3
    rotation_deg: Vec3
    lens: LensSpec
    focus_distance_cm: Optional[float] = None

    def validate(self) -> CameraSpec:
        if not self.label.strip():
            raise ValidationError("camera label cannot be blank")
        _vec3("location_cm", self.location_cm)
        _vec3("rotation_deg", self.rotation_deg)
        self.lens.validate()
        if self.focus_distance_cm is not None:
            _positive("focus_distance_cm", self.focus_distance_cm)
        return self


@dataclass(frozen=True)
class AtmosphereSpec:
    sun_intensity: float
    sun_color: Color
    sun_rotation_deg: Vec3
    sun_temperature_k: float
    skylight_color: Color
    skylight_intensity: float
    fog_density: float
    fog_height_falloff: float
    fog_color: Color
    fog_start_distance_cm: float
    volumetric_fog: bool
    rayleigh_scale: float
    mie_scale: float
    mie_anisotropy: float
    exposure_bias: float
    bloom_intensity: float

    def validate(self) -> AtmosphereSpec:
        _positive("sun_intensity", self.sun_intensity, allow_zero=True)
        _color("sun_color", self.sun_color)
        _vec3("sun_rotation_deg", self.sun_rotation_deg)
        _positive("sun_temperature_k", self.sun_temperature_k)
        _color("skylight_color", self.skylight_color)
        _positive("skylight_intensity", self.skylight_intensity, allow_zero=True)
        _positive("fog_density", self.fog_density, allow_zero=True)
        _positive("fog_height_falloff", self.fog_height_falloff, allow_zero=True)
        _color("fog_color", self.fog_color)
        _positive("fog_start_distance_cm", self.fog_start_distance_cm, allow_zero=True)
        _positive("rayleigh_scale", self.rayleigh_scale, allow_zero=True)
        _positive("mie_scale", self.mie_scale, allow_zero=True)
        anisotropy = _finite("mie_anisotropy", self.mie_anisotropy)
        if not -1.0 <= anisotropy <= 1.0:
            raise ValidationError("mie_anisotropy must be between -1 and 1")
        _finite("exposure_bias", self.exposure_bias)
        _positive("bloom_intensity", self.bloom_intensity, allow_zero=True)
        return self

    def with_overrides(self, overrides: Mapping[str, Any]) -> AtmosphereSpec:
        unknown = sorted(set(overrides) - set(asdict(self)))
        if unknown:
            raise ValidationError(f"unknown atmosphere override(s): {', '.join(unknown)}")
        return replace(self, **dict(overrides)).validate()


@dataclass(frozen=True)
class WindSpec:
    strength: float
    speed: float
    minimum_gust: float

    def validate(self) -> WindSpec:
        _positive("strength", self.strength, allow_zero=True)
        _positive("speed", self.speed, allow_zero=True)
        _positive("minimum_gust", self.minimum_gust, allow_zero=True)
        return self


@dataclass(frozen=True)
class NiagaraSpec:
    asset_path: str
    label: str
    location_cm: Vec3 = (0.0, 0.0, 0.0)
    rotation_deg: Vec3 = (0.0, 0.0, 0.0)
    scale: Vec3 = (1.0, 1.0, 1.0)
    auto_destroy: bool = False

    def validate(self) -> NiagaraSpec:
        if not self.asset_path.startswith("/Game/"):
            raise ValidationError("Niagara asset_path must start with /Game/")
        if not self.label.strip():
            raise ValidationError("Niagara label cannot be blank")
        _vec3("location_cm", self.location_cm)
        _vec3("rotation_deg", self.rotation_deg)
        scale = _vec3("scale", self.scale)
        if any(part <= 0 for part in scale):
            raise ValidationError("Niagara scale components must be positive")
        return self
