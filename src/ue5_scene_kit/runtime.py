"""Runtime boundary between ordinary Python and Unreal's embedded module."""
from __future__ import annotations

from types import ModuleType
from typing import Any, Optional

from .errors import UnrealUnavailableError

_override: Optional[Any] = None


def set_unreal_module(module: Optional[Any]) -> None:
    """Inject an Unreal-compatible module, primarily for tests and adapters."""
    global _override
    _override = module


def get_unreal() -> Any:
    """Return Unreal's Python module or raise an actionable error.

    Imports are intentionally lazy so preset validation, manifests, and unit
    tests work on laptops and CI runners that do not have Unreal installed.
    """
    if _override is not None:
        return _override
    try:
        import unreal  # type: ignore[import-not-found]
    except ImportError as exc:
        raise UnrealUnavailableError(
            "This operation must run inside Unreal Editor's embedded Python. "
            "Use `UnrealEditor-Cmd <project> -ExecutePythonScript=<script>` "
            "or inject a compatible test double with set_unreal_module()."
        ) from exc
    if not isinstance(unreal, ModuleType) and not hasattr(unreal, "EditorLevelLibrary"):
        raise UnrealUnavailableError("Imported `unreal` module is not the Unreal Editor API")
    return unreal

