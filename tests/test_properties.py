import pytest
from conftest import ClampPropertyObject, FakePropertyObject, InertPropertyObject

from ue5_scene_kit.errors import (
    InertPropertyError,
    PhantomPropertyError,
    PropertyConformanceError,
)
from ue5_scene_kit.properties import read_property, set_and_verify


def test_set_and_verify_returns_receipt():
    obj = FakePropertyObject(exposure=1.0)
    receipt = set_and_verify(obj, "exposure", 2.0)
    assert receipt == {
        "name": "exposure",
        "asked": 2.0,
        "before": 1.0,
        "landed": 2.0,
        "conformed": True,
        "changed": True,
    }


def test_missing_property_is_typed():
    with pytest.raises(PhantomPropertyError, match="missing"):
        read_property(FakePropertyObject(), "missing")


def test_inert_property_is_rejected():
    with pytest.raises(InertPropertyError, match="did not move"):
        set_and_verify(InertPropertyObject(exposure=1.0), "exposure", 2.0)


def test_reasserting_current_value_is_valid():
    receipt = set_and_verify(InertPropertyObject(exposure=1.0), "exposure", 1.0)
    assert receipt["conformed"] is True
    assert receipt["changed"] is False


def test_clamp_requires_explicit_permission(fake_unreal):
    obj = ClampPropertyObject(value=1.0)
    with pytest.raises(PropertyConformanceError, match="did not land"):
        set_and_verify(obj, "value", 20.0)
    obj = ClampPropertyObject(value=1.0)
    receipt = set_and_verify(obj, "value", 20.0, allow_clamp=True)
    assert receipt["landed"] == 10.0
    assert receipt["conformed"] is False

