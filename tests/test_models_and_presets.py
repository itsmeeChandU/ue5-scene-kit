import json

import pytest

from ue5_scene_kit import __version__
from ue5_scene_kit.__main__ import main
from ue5_scene_kit.atmosphere import resolve_atmosphere
from ue5_scene_kit.errors import ValidationError
from ue5_scene_kit.models import AtmosphereSpec, LensSpec, NiagaraSpec
from ue5_scene_kit.presets import list_presets


def test_version_and_discovery_are_stable():
    assert __version__ == "0.1.0"
    presets = list_presets()
    assert "golden_hour" in presets["atmospheres"]
    assert "standard" in presets["lenses"]
    assert "rain_storm" in presets["weather"]


def test_all_atmosphere_presets_validate():
    for name in list_presets()["atmospheres"]:
        assert isinstance(resolve_atmosphere(name), AtmosphereSpec)


def test_override_is_immutable_and_validated():
    base = resolve_atmosphere("overcast")
    changed = resolve_atmosphere("overcast", {"fog_density": 0.25})
    assert base.fog_density == 0.1
    assert changed.fog_density == 0.25
    with pytest.raises(ValidationError, match="unknown atmosphere override"):
        resolve_atmosphere("overcast", {"invented_knob": 1})


@pytest.mark.parametrize(
    "spec",
    [LensSpec(0, 2.8), LensSpec(50, 0), NiagaraSpec("/Plugin/NS_Rain", "rain")],
)
def test_invalid_specs_fail_loudly(spec):
    with pytest.raises(ValidationError):
        spec.validate()


def test_cli_validate_emits_json(capsys):
    assert main(["validate"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result == {"atmospheres": 6, "lenses": 4, "winds": 4}

