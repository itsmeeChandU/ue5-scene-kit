"""Fail-loud Unreal editor-property writes with read-back receipts.

Unreal's Python API can fail in four costly ways: a guessed property name can
raise, an engine clamp can change the requested value, a struct copy can be
mutated without being assigned to its owner, and a setter can return while the
old value remains. ``set_and_verify`` turns those states into explicit results
or typed exceptions instead of allowing an incorrect scene to render.
"""
from __future__ import annotations

from typing import Any, Optional

from .errors import InertPropertyError, PhantomPropertyError, PropertyConformanceError
from .runtime import get_unreal

_UNCOMPARABLE = object()


def _log(message: str) -> None:
    try:
        get_unreal().log_warning(f"ue5_scene_kit: {message}")
    except Exception:
        print(f"ue5_scene_kit: {message}")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _snapshot(value: Any) -> Any:
    copier = getattr(value, "copy", None)
    if not callable(copier):
        return value
    try:
        return copier()
    except TypeError:
        _log(f"{type(value).__name__}.copy() needs arguments; using the original value")
        return value


def _structural(value: Any, depth: int = 0) -> Any:
    if depth > 8:
        return _UNCOMPARABLE
    if value is None or isinstance(value, (str, bytes, bool)) or _is_number(value):
        return value
    to_tuple = getattr(value, "to_tuple", None)
    if callable(to_tuple):
        try:
            return tuple(_structural(item, depth + 1) for item in to_tuple())
        except Exception:
            return _UNCOMPARABLE
    if isinstance(value, (list, tuple)) or type(value).__name__ in {
        "Array",
        "FixedArray",
        "Set",
    }:
        try:
            return tuple(_structural(item, depth + 1) for item in value)
        except Exception:
            return _UNCOMPARABLE
    return value


def _equal(left: Any, right: Any, tolerance: Optional[float]) -> bool:
    if tolerance is not None and _is_number(left) and _is_number(right):
        return abs(float(left) - float(right)) <= tolerance
    try:
        if bool(left == right):
            return True
    except Exception as exc:
        raise PropertyConformanceError(
            f"Cannot compare {left!r} and {right!r}: {exc}. Compare a verified struct field."
        ) from exc
    left_value = _structural(left)
    right_value = _structural(right)
    if left_value is _UNCOMPARABLE or right_value is _UNCOMPARABLE:
        return False
    return left_value == right_value


def _default_tolerance(value: Any) -> Optional[float]:
    if isinstance(value, float):
        return 1e-4 * max(1.0, abs(value))
    return None


def read_property(obj: Any, name: str) -> Any:
    """Read an editor property and normalize missing-name failures."""
    try:
        return obj.get_editor_property(name)
    except Exception as exc:
        raise PhantomPropertyError(
            f"'{name}' is not a readable editor property on {type(obj).__name__}: {exc}"
        ) from exc


def set_and_verify(
    obj: Any,
    name: str,
    value: Any,
    *,
    tolerance: Optional[float] = None,
    allow_clamp: bool = False,
) -> dict[str, Any]:
    """Set an editor property, read it back, and return a conformance receipt.

    ``allow_clamp`` is intended only for engine clamps that the caller has
    deliberately accepted. Even then, the returned ``landed`` value is truth.
    A write that does not change a differing old value always raises.
    """
    before = _snapshot(read_property(obj, name))
    try:
        obj.set_editor_property(name, value)
    except Exception as exc:
        raise PropertyConformanceError(
            f"'{name}' on {type(obj).__name__} was readable ({before!r}) "
            f"but rejected {value!r}: {exc}"
        ) from exc
    try:
        landed = obj.get_editor_property(name)
    except Exception as exc:
        raise PropertyConformanceError(
            f"'{name}' on {type(obj).__name__} became unreadable after its write: {exc}"
        ) from exc

    resolved_tolerance = tolerance if tolerance is not None else _default_tolerance(value)
    conformed = _equal(landed, value, resolved_tolerance)
    changed = not _equal(landed, before, resolved_tolerance)
    already_at_target = _equal(before, value, resolved_tolerance)
    receipt = {
        "name": name,
        "asked": value,
        "before": before,
        "landed": landed,
        "conformed": conformed,
        "changed": changed,
    }
    if not changed and not already_at_target:
        raise InertPropertyError(
            f"'{name}' on {type(obj).__name__} did not move: asked {value!r}, "
            f"before {before!r}, after {landed!r}"
        )
    if not conformed:
        if not allow_clamp:
            raise PropertyConformanceError(
                f"'{name}' on {type(obj).__name__} did not land: asked {value!r}, "
                f"engine returned {landed!r} (before {before!r})"
            )
        _log(f"CLAMPED {name}: asked {value!r}, landed {landed!r}")
    return receipt


def write_struct_fields(owner: Any, property_name: str, **fields: Any) -> dict[str, Any]:
    """Safely mutate a struct-valued property and assign it back to its owner."""
    struct = read_property(owner, property_name)
    for name, value in fields.items():
        set_and_verify(struct, name, value, allow_clamp=False)
    receipt = set_and_verify(owner, property_name, struct, allow_clamp=False)
    committed = read_property(owner, property_name)
    for name, value in fields.items():
        landed = read_property(committed, name)
        if not _equal(landed, value, _default_tolerance(value)):
            raise PropertyConformanceError(
                f"struct write-back lost {property_name}.{name}: asked {value!r}, "
                f"landed {landed!r}"
            )
    return receipt

