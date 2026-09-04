import math

import pytest

from ue5_scene_kit.cameras import (
    camera_spec,
    coverage_specs,
    look_at_rotation,
    spawn_camera,
)
from ue5_scene_kit.errors import ValidationError


def test_look_at_axis_aligned():
    assert look_at_rotation((0, 0, 0), (100, 0, 0)) == (0.0, 0.0, 0.0)
    pitch, yaw, roll = look_at_rotation((0, 0, 0), (0, 100, 100))
    assert math.isclose(pitch, 45.0)
    assert math.isclose(yaw, 90.0)
    assert roll == 0.0


def test_identical_camera_and_target_rejected():
    with pytest.raises(ValidationError, match="identical"):
        look_at_rotation((1, 2, 3), (1, 2, 3))


def test_coverage_has_three_distinct_lenses():
    specs = coverage_specs("Subject", (0, 0, 100))
    assert [spec.label for spec in specs] == ["Subject_Wide", "Subject_Medium", "Subject_Close"]
    assert [spec.lens.focal_length_mm for spec in specs] == [24.0, 50.0, 85.0]


def test_unknown_lens_rejected():
    with pytest.raises(ValidationError, match="unknown lens"):
        camera_spec("Camera", location_cm=(100, 0, 0), target_cm=(0, 0, 0), lens="magic")


def test_spawn_camera_commits_lens_and_focus(fake_unreal):
    spec = camera_spec(
        "Hero", location_cm=(300, 0, 100), target_cm=(0, 0, 100), lens="short_tele"
    )
    actor = spawn_camera(spec)
    assert actor.label == "Hero"
    assert actor.camera_component.get_editor_property("current_focal_length") == 85.0
    focus = actor.camera_component.get_editor_property("focus_settings")
    assert focus.get_editor_property("focus_method") == "MANUAL"
    assert focus.get_editor_property("manual_focus_distance") == 300.0

