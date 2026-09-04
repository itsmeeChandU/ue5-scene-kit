"""Live Unreal Editor smoke test; writes a machine-readable receipt."""
from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

import unreal

ROOT = Path(os.environ.get("SCENE_KIT_ROOT", Path(__file__).resolve().parents[1]))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ue5_scene_kit import build_foundation, save_current_level  # noqa: E402
from ue5_scene_kit.weather import build_weather  # noqa: E402

RECEIPT = Path(os.environ.get("SCENE_KIT_RECEIPT", ROOT / "smoke-receipt.json"))
EXPECTED_FOUNDATION_LABELS = {
    "SceneKit_Sun_golden_hour",
    "SceneKit_Sky_golden_hour",
    "SceneKit_SkyLight_golden_hour",
    "SceneKit_Fog_golden_hour",
    "SceneKit_PostProcess_golden_hour",
    "SceneKit_Wind",
    "Smoke_Wide",
    "Smoke_Medium",
    "Smoke_Close",
}


def _engine_version() -> str:
    return str(unreal.SystemLibrary.get_engine_version())


def _labels() -> set[str]:
    return {
        actor.get_actor_label()
        for actor in unreal.EditorLevelLibrary.get_all_level_actors()
    }


def _write(payload: dict) -> None:
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    receipt = {
        "schema_version": 1,
        "status": "FAIL",
        "engine_version": _engine_version(),
        "project": str(unreal.Paths.get_project_file_path()),
        "checks": {},
    }
    try:
        created = unreal.EditorLevelLibrary.new_level("/Game/SceneKitSmoke")
        if not created:
            raise RuntimeError("EditorLevelLibrary.new_level returned false")
        receipt["checks"]["new_level"] = "PASS"

        foundation = build_foundation(
            target_cm=(0.0, 0.0, 100.0),
            atmosphere="golden_hour",
            wind="breeze",
            camera_prefix="Smoke",
        )
        labels = _labels()
        missing = sorted(EXPECTED_FOUNDATION_LABELS - labels)
        if missing:
            raise RuntimeError(f"foundation actors missing from level: {missing}")
        receipt["checks"]["foundation_actor_count"] = len(labels)
        receipt["checks"]["foundation_labels"] = "PASS"

        focal_lengths = [
            float(camera.camera_component.get_editor_property("current_focal_length"))
            for camera in foundation.cameras
        ]
        if focal_lengths != [24.0, 50.0, 85.0]:
            raise RuntimeError(f"unexpected camera focal lengths: {focal_lengths}")
        receipt["checks"]["camera_focal_lengths_mm"] = focal_lengths

        focus_distances = [
            float(
                camera.camera_component.get_editor_property("focus_settings").get_editor_property(
                    "manual_focus_distance"
                )
            )
            for camera in foundation.cameras
        ]
        if any(distance <= 0 for distance in focus_distances):
            raise RuntimeError(f"invalid focus distances: {focus_distances}")
        receipt["checks"]["camera_focus_distances_cm"] = focus_distances

        weather = build_weather("overcast_misty", label_prefix="WeatherSmoke")
        if weather["vfx"] is not None:
            raise RuntimeError("overcast_misty unexpectedly spawned a VFX asset")
        receipt["checks"]["weather_composition"] = "PASS"

        save_current_level(confirmed=True)
        map_filename = Path(unreal.Paths.convert_relative_path_to_full(
            unreal.Paths.project_content_dir() + "SceneKitSmoke.umap"
        ))
        if not map_filename.is_file() or map_filename.stat().st_size == 0:
            raise RuntimeError(f"saved map missing or empty: {map_filename}")
        receipt["checks"]["saved_map_bytes"] = map_filename.stat().st_size

        receipt["status"] = "PASS"
        _write(receipt)
        unreal.log(f"SCENE_KIT_SMOKE_PASS receipt={RECEIPT}")
    except Exception as exc:
        receipt["error_type"] = type(exc).__name__
        receipt["error"] = str(exc)
        receipt["traceback"] = traceback.format_exc()
        _write(receipt)
        unreal.log_error(f"SCENE_KIT_SMOKE_FAIL receipt={RECEIPT}: {exc}")
        raise


main()
