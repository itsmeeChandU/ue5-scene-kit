"""Run inside Unreal Editor after making `src/` importable."""
from ue5_scene_kit import build_foundation

foundation = build_foundation(
    target_cm=(0.0, 0.0, 100.0),
    atmosphere="golden_hour",
    wind="breeze",
    camera_prefix="Temple",
)

print(f"Built {len(foundation.cameras)} cameras; inspect the level before saving.")

