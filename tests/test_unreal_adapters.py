import pytest
from conftest import FakeEditorAssetLibrary, FakeEditorLevelLibrary

from ue5_scene_kit.atmosphere import build_atmosphere
from ue5_scene_kit.errors import MissingAssetError, UnrealUnavailableError, ValidationError
from ue5_scene_kit.models import NiagaraSpec
from ue5_scene_kit.niagara import NiagaraRegistry, spawn_niagara
from ue5_scene_kit.runtime import get_unreal
from ue5_scene_kit.scene import save_current_level
from ue5_scene_kit.weather import build_weather
from ue5_scene_kit.wind import spawn_wind


def test_off_engine_operation_has_actionable_error():
    with pytest.raises(UnrealUnavailableError, match="embedded Python"):
        get_unreal()


def test_build_atmosphere_spawns_complete_foundation(fake_unreal):
    result = build_atmosphere("golden_hour")
    assert set(result) == {"sun", "sky", "skylight", "fog", "post_process", "preset", "spec"}
    assert len(FakeEditorLevelLibrary.actors) == 5
    assert result["sun"].label == "SceneKit_Sun_golden_hour"
    assert result["post_process"].get_editor_property("unbound") is True


def test_wind_writes_all_configured_properties(fake_unreal):
    actor = spawn_wind("storm", yaw_deg=30)
    assert actor.component.get_editor_property("strength") == 2.5
    assert actor.component.get_editor_property("speed") == 3.5
    assert actor.component.get_editor_property("min_gust_amount") == 1.2


def test_registry_does_not_assume_project_assets():
    registry = NiagaraRegistry()
    with pytest.raises(ValidationError, match="unknown Niagara intent"):
        registry.resolve("rain")
    registry.register("rain", "/Game/MyProject/NS_Rain")
    assert registry.resolve("rain") == "/Game/MyProject/NS_Rain"


def test_niagara_missing_asset_is_typed(fake_unreal):
    spec = NiagaraSpec("/Game/MyProject/NS_Rain", "Rain")
    with pytest.raises(MissingAssetError, match="does not exist"):
        spawn_niagara(spec)


def test_niagara_spawns_serializable_actor(fake_unreal):
    asset = object()
    FakeEditorAssetLibrary.assets["/Game/MyProject/NS_Rain"] = asset
    component = spawn_niagara(NiagaraSpec("/Game/MyProject/NS_Rain", "Rain"))
    assert component.asset is asset
    assert FakeEditorLevelLibrary.actors[-1].label == "Rain"


def test_save_is_explicit(fake_unreal):
    with pytest.raises(ValidationError, match="confirmed"):
        save_current_level()
    save_current_level(confirmed=True)


def test_weather_requires_vfx_registry_before_spawning(fake_unreal):
    with pytest.raises(ValidationError, match="requires a project-owned Niagara intent"):
        build_weather("rain_light")
    assert FakeEditorLevelLibrary.actors == []


def test_clear_weather_builds_atmosphere_and_wind(fake_unreal):
    result = build_weather("golden_clear")
    assert result["weather"] == "golden_clear"
    assert result["vfx"] is None
    assert len(FakeEditorLevelLibrary.actors) == 6


def test_weather_with_registered_vfx(fake_unreal):
    asset = object()
    FakeEditorAssetLibrary.assets["/Game/MyProject/NS_Rain"] = asset
    registry = NiagaraRegistry({"rain": "/Game/MyProject/NS_Rain"})
    result = build_weather("rain_light", vfx_registry=registry)
    assert result["vfx"].asset is asset
    assert len(FakeEditorLevelLibrary.actors) == 7
