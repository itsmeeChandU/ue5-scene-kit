"""Conservative starting presets. Treat them as authored defaults, not truth."""
from __future__ import annotations

from .models import AtmosphereSpec, LensSpec, WindSpec

LENSES = {
    "wide": LensSpec(24.0, 4.0),
    "standard": LensSpec(50.0, 2.8),
    "short_tele": LensSpec(85.0, 2.0),
    "hero_close": LensSpec(135.0, 1.8),
}

ATMOSPHERES = {
    "golden_hour": AtmosphereSpec(
        10.0, (1.0, 0.72, 0.38, 1.0), (-25.0, 225.0, 0.0), 3200.0,
        (1.0, 0.85, 0.65, 1.0), 1.0, 0.02, 0.2, (0.85, 0.55, 0.22, 1.0),
        100.0, False, 0.0331, 0.008, 0.8, 4.0, 0.5,
    ),
    "dawn": AtmosphereSpec(
        6.0, (1.0, 0.8, 0.55, 1.0), (-8.0, 90.0, 0.0), 4000.0,
        (0.85, 0.75, 0.85, 1.0), 1.0, 0.06, 0.2, (0.55, 0.5, 0.55, 1.0),
        100.0, True, 0.0331, 0.018, 0.75, 4.0, 0.7,
    ),
    "noon": AtmosphereSpec(
        20.0, (1.0, 0.97, 0.94, 1.0), (-65.0, 180.0, 0.0), 5500.0,
        (1.0, 1.0, 1.0, 1.0), 1.0, 0.015, 0.2, (0.85, 0.9, 0.95, 1.0),
        100.0, False, 0.0331, 0.005, 0.8, 2.0, 0.3,
    ),
    "overcast": AtmosphereSpec(
        8.0, (0.95, 0.95, 0.95, 1.0), (-55.0, 180.0, 0.0), 6500.0,
        (0.9, 0.9, 0.95, 1.0), 1.0, 0.1, 0.2, (0.7, 0.72, 0.78, 1.0),
        100.0, True, 0.05, 0.04, 0.6, 3.0, 0.4,
    ),
    "dusk": AtmosphereSpec(
        5.0, (1.0, 0.55, 0.3, 1.0), (-10.0, 220.0, 0.0), 2700.0,
        (0.85, 0.55, 0.35, 1.0), 1.0, 0.04, 0.2, (0.45, 0.2, 0.1, 1.0),
        100.0, True, 0.0331, 0.02, 0.85, 4.0, 0.8,
    ),
    "night": AtmosphereSpec(
        0.3, (0.4, 0.5, 0.85, 1.0), (-45.0, 90.0, 0.0), 7500.0,
        (0.2, 0.3, 0.5, 1.0), 1.0, 0.05, 0.2, (0.1, 0.15, 0.25, 1.0),
        100.0, True, 0.0331, 0.012, 0.7, 6.0, 1.5,
    ),
}

WINDS = {
    "calm": WindSpec(0.05, 0.05, 0.02),
    "breeze": WindSpec(0.30, 0.40, 0.10),
    "wind": WindSpec(0.80, 1.20, 0.30),
    "storm": WindSpec(2.50, 3.50, 1.20),
}

WEATHER = {
    "sunny_clear": ("noon", {}, "calm", None),
    "golden_clear": ("golden_hour", {}, "calm", None),
    "overcast_dry": ("overcast", {}, "breeze", None),
    "overcast_misty": ("overcast", {"fog_density": 0.12}, "breeze", None),
    "rain_light": (
        "overcast", {"fog_density": 0.08, "volumetric_fog": True}, "breeze", "rain",
    ),
    "rain_storm": (
        "overcast", {"fog_density": 0.18, "volumetric_fog": True}, "storm", "rain",
    ),
    "snow_fall": ("overcast", {"fog_density": 0.10}, "breeze", "snow"),
    "fog_dense": (
        "overcast", {"fog_density": 0.30, "volumetric_fog": True}, "calm", None,
    ),
    "dust_storm": (
        "dusk", {"fog_density": 0.20, "fog_color": (0.55, 0.45, 0.30, 1.0)},
        "storm", "dust",
    ),
    "moonlit_clear": ("night", {}, "calm", None),
}


def list_presets() -> dict[str, list[str]]:
    """Return stable, sorted preset names for discovery and tooling."""
    return {
        "atmospheres": sorted(ATMOSPHERES),
        "lenses": sorted(LENSES),
        "weather": sorted(WEATHER),
        "winds": sorted(WINDS),
    }

