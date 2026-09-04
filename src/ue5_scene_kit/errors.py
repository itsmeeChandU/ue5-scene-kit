"""Public exception hierarchy for UE5 Scene Kit."""


class SceneKitError(RuntimeError):
    """Base class for errors raised by the package."""


class UnrealUnavailableError(SceneKitError):
    """The operation needs Unreal's embedded Python runtime."""


class ValidationError(SceneKitError, ValueError):
    """A caller supplied an invalid scene specification."""


class PropertyConformanceError(SceneKitError):
    """An Unreal property write failed or did not read back as requested."""


class PhantomPropertyError(PropertyConformanceError, AttributeError):
    """The requested Unreal editor property is missing or unreadable."""


class InertPropertyError(PropertyConformanceError):
    """A write returned successfully but left the old value in place."""


class MissingAssetError(SceneKitError, FileNotFoundError):
    """An Unreal content path could not be loaded."""

