from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from ue5_scene_kit.runtime import set_unreal_module


class FakePropertyObject:
    def __init__(self, **properties):
        self._properties = dict(properties)

    def get_editor_property(self, name):
        if name not in self._properties:
            raise AttributeError(name)
        return self._properties[name]

    def set_editor_property(self, name, value):
        if name not in self._properties:
            raise AttributeError(name)
        self._properties[name] = value


class InertPropertyObject(FakePropertyObject):
    def set_editor_property(self, name, value):
        if name not in self._properties:
            raise AttributeError(name)


class ClampPropertyObject(FakePropertyObject):
    def set_editor_property(self, name, value):
        if name not in self._properties:
            raise AttributeError(name)
        self._properties[name] = min(float(value), 10.0)


@dataclass(eq=True)
class Vector:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass(eq=True)
class Rotator:
    pitch: float = 0.0
    yaw: float = 0.0
    roll: float = 0.0


@dataclass(eq=True)
class LinearColor:
    r: float
    g: float
    b: float
    a: float


class FakeActor(FakePropertyObject):
    def __init__(self, kind):
        super().__init__(unbound=False, settings=FakeSettings())
        self.kind = kind
        self.label = None
        self.scale = None
        self.component = FakePropertyObject(strength=0.0, speed=0.0, min_gust_amount=0.0)
        self.light_component = FakeLightComponent()
        self.camera_component = FakeCameraComponent()
        self.niagara_component = FakeNiagaraComponent()
        self._sky = FakePropertyObject(
            rayleigh_scattering_scale=0.0,
            mie_scattering_scale=0.0,
            mie_anisotropy=0.0,
        )
        self._fog = FakePropertyObject(
            fog_density=0.0,
            fog_height_falloff=0.0,
            fog_inscattering_luminance=None,
            start_distance=0.0,
            enable_volumetric_fog=False,
        )

    def set_actor_label(self, label):
        self.label = label

    @property
    def settings(self):
        return self.get_editor_property("settings")

    def set_actor_scale3d(self, scale):
        self.scale = scale

    def set_destroy_on_system_finish(self, value):
        self.auto_destroy = value

    def get_component_by_class(self, kind):
        return self._sky if kind is SkyAtmosphereComponent else self._fog


class FakeLightComponent(FakePropertyObject):
    def __init__(self):
        super().__init__(
            atmosphere_sun_light=False,
            use_temperature=False,
            temperature=6500.0,
            cast_shadows=False,
            source_type=None,
            real_time_capture=False,
        )

    def set_intensity(self, value):
        self.intensity = value

    def set_light_color(self, value):
        self.color = value


class FakeFocus(FakePropertyObject):
    def __init__(self):
        super().__init__(focus_method="AUTO", manual_focus_distance=100000.0)

    def copy(self):
        return FakeFocus.from_values(self._properties)

    @classmethod
    def from_values(cls, values):
        item = cls()
        item._properties.update(values)
        return item

    def to_tuple(self):
        return tuple(self._properties.values())


class FakeCameraComponent(FakePropertyObject):
    def __init__(self):
        super().__init__(
            current_focal_length=35.0,
            current_aperture=5.6,
            focus_settings=FakeFocus(),
        )


class FakeSettings(FakePropertyObject):
    def __init__(self):
        super().__init__(
            override_auto_exposure_method=False,
            auto_exposure_method="AUTO",
            override_auto_exposure_bias=False,
            auto_exposure_bias=0.0,
            override_bloom_intensity=False,
            bloom_intensity=0.0,
        )

    def copy(self):
        copied = FakeSettings()
        copied._properties.update(self._properties)
        return copied

    def to_tuple(self):
        return tuple(self._properties.values())


class FakeNiagaraComponent:
    def __init__(self):
        self.asset = None

    def set_asset(self, asset, reset):
        self.asset = asset


class SkyAtmosphereComponent:
    pass


class ExponentialHeightFogComponent:
    pass


class FakeEditorLevelLibrary:
    actors = []
    save_result = True

    @classmethod
    def spawn_actor_from_class(cls, kind, location, rotation):
        actor = FakeActor(kind)
        cls.actors.append(actor)
        return actor

    @classmethod
    def save_current_level(cls):
        return cls.save_result


class FakeEditorAssetLibrary:
    assets = {}

    @classmethod
    def load_asset(cls, path):
        return cls.assets.get(path)


def build_fake_unreal():
    FakeEditorLevelLibrary.actors = []
    FakeEditorLevelLibrary.save_result = True
    FakeEditorAssetLibrary.assets = {}
    return SimpleNamespace(
        Vector=Vector,
        Rotator=Rotator,
        LinearColor=LinearColor,
        EditorLevelLibrary=FakeEditorLevelLibrary,
        EditorAssetLibrary=FakeEditorAssetLibrary,
        CineCameraActor=type("CineCameraActor", (), {}),
        DirectionalLight=type("DirectionalLight", (), {}),
        SkyAtmosphere=type("SkyAtmosphere", (), {}),
        SkyLight=type("SkyLight", (), {}),
        ExponentialHeightFog=type("ExponentialHeightFog", (), {}),
        PostProcessVolume=type("PostProcessVolume", (), {}),
        WindDirectionalSource=type("WindDirectionalSource", (), {}),
        NiagaraActor=type("NiagaraActor", (), {}),
        SkyAtmosphereComponent=SkyAtmosphereComponent,
        ExponentialHeightFogComponent=ExponentialHeightFogComponent,
        CameraFocusMethod=SimpleNamespace(MANUAL="MANUAL"),
        SkyLightSourceType=SimpleNamespace(SLS_CAPTURED_SCENE="CAPTURED"),
        AutoExposureMethod=SimpleNamespace(AEM_MANUAL="MANUAL"),
        log_warning=lambda message: None,
    )


@pytest.fixture
def fake_unreal():
    module = build_fake_unreal()
    set_unreal_module(module)
    yield module
    set_unreal_module(None)
