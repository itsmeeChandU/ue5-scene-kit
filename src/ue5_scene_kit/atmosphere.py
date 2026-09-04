"""Build a cinematic sun, sky, skylight, fog, and post-process foundation."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Optional

from .errors import ValidationError
from .models import AtmosphereSpec
from .presets import ATMOSPHERES
from .properties import read_property, set_and_verify
from .runtime import get_unreal


def resolve_atmosphere(
    preset: str = "golden_hour", overrides: Optional[Mapping[str, Any]] = None
) -> AtmosphereSpec:
    """Resolve and validate a preset without requiring Unreal."""
    if preset not in ATMOSPHERES:
        raise ValidationError(f"unknown atmosphere {preset!r}; available: {sorted(ATMOSPHERES)}")
    spec = ATMOSPHERES[preset]
    return spec.with_overrides(overrides or {})


def build_atmosphere(
    preset: str = "golden_hour",
    *,
    overrides: Optional[Mapping[str, Any]] = None,
    label_prefix: str = "SceneKit",
) -> dict[str, Any]:
    """Spawn a complete lighting/atmosphere foundation in the current level.

    The returned mapping contains each actor plus the fully resolved spec.
    Callers own level saving; this function never saves or overwrites a map.
    """
    spec = resolve_atmosphere(preset, overrides)
    ue = get_unreal()
    spawn = ue.EditorLevelLibrary.spawn_actor_from_class

    sun = spawn(
        ue.DirectionalLight,
        ue.Vector(0.0, 0.0, 1000.0),
        ue.Rotator(
            pitch=spec.sun_rotation_deg[0],
            yaw=spec.sun_rotation_deg[1],
            roll=spec.sun_rotation_deg[2],
        ),
    )
    sun.set_actor_label(f"{label_prefix}_Sun_{preset}")
    sun_component = sun.light_component
    sun_component.set_intensity(spec.sun_intensity)
    sun_component.set_light_color(ue.LinearColor(*spec.sun_color))
    for name, value in (
        ("atmosphere_sun_light", True),
        ("use_temperature", True),
        ("temperature", spec.sun_temperature_k),
        ("cast_shadows", True),
    ):
        set_and_verify(sun_component, name, value)

    sky = spawn(ue.SkyAtmosphere, ue.Vector(), ue.Rotator())
    sky.set_actor_label(f"{label_prefix}_Sky_{preset}")
    sky_component = sky.get_component_by_class(ue.SkyAtmosphereComponent)
    if sky_component is None:
        raise RuntimeError("SkyAtmosphere spawned without a SkyAtmosphereComponent")
    for name, value in (
        ("rayleigh_scattering_scale", spec.rayleigh_scale),
        ("mie_scattering_scale", spec.mie_scale),
        ("mie_anisotropy", spec.mie_anisotropy),
    ):
        set_and_verify(sky_component, name, value, allow_clamp=True)

    skylight = spawn(ue.SkyLight, ue.Vector(0.0, 0.0, 500.0), ue.Rotator())
    skylight.set_actor_label(f"{label_prefix}_SkyLight_{preset}")
    skylight_component = skylight.light_component
    set_and_verify(
        skylight_component, "source_type", ue.SkyLightSourceType.SLS_CAPTURED_SCENE
    )
    set_and_verify(skylight_component, "real_time_capture", True)
    skylight_component.set_intensity(spec.skylight_intensity)
    skylight_component.set_light_color(ue.LinearColor(*spec.skylight_color))

    fog = spawn(ue.ExponentialHeightFog, ue.Vector(), ue.Rotator())
    fog.set_actor_label(f"{label_prefix}_Fog_{preset}")
    fog_component = fog.get_component_by_class(ue.ExponentialHeightFogComponent)
    if fog_component is None:
        raise RuntimeError("ExponentialHeightFog spawned without its component")
    for name, value in (
        ("fog_density", spec.fog_density),
        ("fog_height_falloff", spec.fog_height_falloff),
        ("fog_inscattering_luminance", ue.LinearColor(*spec.fog_color)),
        ("start_distance", spec.fog_start_distance_cm),
        ("enable_volumetric_fog", spec.volumetric_fog),
    ):
        set_and_verify(fog_component, name, value, allow_clamp=True)

    post = spawn(ue.PostProcessVolume, ue.Vector(0.0, 0.0, 300.0), ue.Rotator())
    post.set_actor_label(f"{label_prefix}_PostProcess_{preset}")
    set_and_verify(post, "unbound", True)
    settings = read_property(post, "settings")
    for name, value in (
        ("override_auto_exposure_method", True),
        ("auto_exposure_method", ue.AutoExposureMethod.AEM_MANUAL),
        ("override_auto_exposure_bias", True),
        ("auto_exposure_bias", spec.exposure_bias),
        ("override_bloom_intensity", True),
        ("bloom_intensity", spec.bloom_intensity),
    ):
        set_and_verify(settings, name, value, allow_clamp=True)
    set_and_verify(post, "settings", settings)

    return {
        "sun": sun,
        "sky": sky,
        "skylight": skylight,
        "fog": fog,
        "post_process": post,
        "preset": preset,
        "spec": spec,
    }
