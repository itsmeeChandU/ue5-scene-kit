"""Reusable Unreal Engine 5 editor-Python scene construction primitives."""

from .atmosphere import build_atmosphere, resolve_atmosphere
from .cameras import camera_spec, coverage_specs, look_at_rotation, spawn_camera
from .errors import (
    InertPropertyError,
    MissingAssetError,
    PhantomPropertyError,
    PropertyConformanceError,
    SceneKitError,
    UnrealUnavailableError,
    ValidationError,
)
from .models import AtmosphereSpec, CameraSpec, LensSpec, NiagaraSpec, WindSpec
from .niagara import NiagaraRegistry, spawn_niagara
from .presets import list_presets
from .properties import set_and_verify
from .scene import build_foundation, save_current_level
from .wind import spawn_wind

__all__ = [
    "AtmosphereSpec", "CameraSpec", "InertPropertyError", "LensSpec",
    "MissingAssetError", "NiagaraRegistry", "NiagaraSpec", "PhantomPropertyError",
    "PropertyConformanceError", "SceneKitError", "UnrealUnavailableError",
    "ValidationError", "WindSpec", "build_atmosphere", "build_foundation",
    "camera_spec", "coverage_specs", "list_presets", "look_at_rotation",
    "resolve_atmosphere", "save_current_level", "set_and_verify", "spawn_camera",
    "spawn_niagara", "spawn_wind",
]

__version__ = "0.2.0"
