"""Build and capture a public proof scene using only built-in Unreal meshes."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import unreal

ROOT = Path(os.environ.get("SCENE_KIT_ROOT", Path(__file__).resolve().parents[1]))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ue5_scene_kit import build_foundation, save_current_level, set_and_verify  # noqa: E402
from ue5_scene_kit.cameras import look_at_rotation  # noqa: E402
from ue5_scene_kit.properties import read_property  # noqa: E402

OUTPUT = Path(os.environ.get("SCENE_KIT_PROOF", ROOT / "ue5.4.4-proof.png"))
PROOF_LEVEL = os.environ.get(
    "SCENE_KIT_PROOF_LEVEL", "/Game/SceneKitProof/ProofScene"
)
MESH_PATHS = {
    "cube": "/Engine/BasicShapes/Cube.Cube",
    "cylinder": "/Engine/BasicShapes/Cylinder.Cylinder",
    "sphere": "/Engine/BasicShapes/Sphere.Sphere",
}
STATE = {"warm": 0, "held": 0, "dwelled": 0, "handle": None}


def _material(name: str, color: tuple[float, float, float, float], roughness: float):
    asset_path = f"/Game/SceneKitProof/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return unreal.EditorAssetLibrary.load_asset(asset_path)

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    material = tools.create_asset(
        name,
        "/Game/SceneKitProof",
        unreal.Material,
        unreal.MaterialFactoryNew(),
    )
    if material is None:
        raise RuntimeError(f"failed to create material {asset_path}")
    base = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -300, 0
    )
    base.set_editor_property("constant", unreal.LinearColor(*color))
    unreal.MaterialEditingLibrary.connect_material_property(
        base, "", unreal.MaterialProperty.MP_BASE_COLOR
    )
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -300, 180
    )
    rough.set_editor_property("r", roughness)
    unreal.MaterialEditingLibrary.connect_material_property(
        rough, "", unreal.MaterialProperty.MP_ROUGHNESS
    )
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def _mesh(
    kind: str,
    label: str,
    location: tuple[float, float, float],
    scale: tuple[float, float, float],
    material,
):
    mesh = unreal.EditorAssetLibrary.load_asset(MESH_PATHS[kind])
    if mesh is None:
        raise RuntimeError(f"missing built-in mesh: {MESH_PATHS[kind]}")
    actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
        mesh, unreal.Vector(*location), unreal.Rotator()
    )
    if actor is None:
        raise RuntimeError(f"failed to spawn {label}")
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    actor.static_mesh_component.set_material(0, material)
    return actor


def _build_scene():
    created = unreal.EditorLevelLibrary.new_level(PROOF_LEVEL)
    if not created:
        raise RuntimeError("failed to create proof level")

    stone = _material("M_ProofStone", (0.18, 0.21, 0.25, 1.0), 0.72)
    bronze = _material("M_ProofBronze", (0.42, 0.17, 0.045, 1.0), 0.38)
    ivory = _material("M_ProofIvory", (0.55, 0.43, 0.28, 1.0), 0.62)

    _mesh("cube", "Proof_Ground", (0.0, 0.0, -40.0), (18.0, 18.0, 0.8), stone)
    _mesh("cube", "Proof_Dais", (0.0, 0.0, 20.0), (5.0, 7.5, 0.4), ivory)
    _mesh("cube", "Proof_LeftPillar", (0.0, -310.0, 300.0), (1.2, 1.2, 5.2), ivory)
    _mesh("cube", "Proof_RightPillar", (0.0, 310.0, 300.0), (1.2, 1.2, 5.2), ivory)
    _mesh("cube", "Proof_Lintel", (0.0, 0.0, 585.0), (1.25, 7.4, 0.7), bronze)
    _mesh("sphere", "Proof_SunDisc", (20.0, 0.0, 585.0), (0.82, 0.82, 0.82), bronze)

    for index, y in enumerate((-650.0, -470.0, 470.0, 650.0), start=1):
        _mesh(
            "cylinder",
            f"Proof_Column_{index:02d}",
            (180.0, y, 180.0),
            (0.62, 0.62, 3.6),
            bronze if index in (1, 4) else ivory,
        )
    for index, (x, y, size) in enumerate(
        ((-360.0, -610.0, 1.8), (-420.0, 560.0, 2.2), (420.0, -520.0, 1.4)),
        start=1,
    ):
        _mesh(
            "sphere",
            f"Proof_Orb_{index:02d}",
            (x, y, 80.0 * size),
            (size, size, size),
            bronze,
        )

    foundation = build_foundation(
        target_cm=(0.0, 0.0, 260.0),
        atmosphere="golden_hour",
        wind="breeze",
        camera_prefix="Proof",
    )
    foundation.atmosphere["sun"].light_component.set_intensity(20.0)
    foundation.atmosphere["skylight"].light_component.set_intensity(1.5)
    post = foundation.atmosphere["post_process"]
    settings = read_property(post, "settings")
    set_and_verify(settings, "auto_exposure_bias", 9.5, allow_clamp=True)
    set_and_verify(post, "settings", settings)
    camera = foundation.cameras[0]
    camera_location = (1900.0, -1900.0, 850.0)
    pitch, yaw, roll = look_at_rotation(camera_location, (0.0, 0.0, 260.0))
    camera.set_actor_location(unreal.Vector(*camera_location), False, False)
    camera.set_actor_rotation(
        unreal.Rotator(pitch=pitch, yaw=yaw, roll=roll), False
    )
    camera.camera_component.set_editor_property("current_focal_length", 35.0)
    camera.camera_component.set_editor_property("current_aperture", 8.0)
    unreal.EditorLevelLibrary.pilot_level_actor(camera)
    save_current_level(confirmed=True)
    return camera


def _capture() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _build_scene()

    def tick(_delta_seconds: float) -> None:
        if STATE["warm"] < 90:
            STATE["warm"] += 1
            return
        if STATE["held"] < 48:
            unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(OUTPUT))
            STATE["held"] += 1
            return
        STATE["dwelled"] += 1
        if STATE["dwelled"] < 16:
            return
        if not OUTPUT.is_file() or OUTPUT.stat().st_size == 0:
            raise RuntimeError(f"proof screenshot missing or empty: {OUTPUT}")
        unreal.log(f"SCENE_KIT_PROOF_PASS path={OUTPUT} bytes={OUTPUT.stat().st_size}")
        unreal.unregister_slate_post_tick_callback(STATE["handle"])
        unreal.SystemLibrary.quit_editor()

    STATE["handle"] = unreal.register_slate_post_tick_callback(tick)


_capture()
