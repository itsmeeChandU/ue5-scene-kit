"""Install the source package into an Unreal project's Python path."""
from __future__ import annotations

import hashlib
import shutil
import tempfile
from pathlib import Path


class InstallError(RuntimeError):
    """Raised when a project installation cannot be completed safely."""


def _resolve_project(project: str | Path) -> tuple[Path, Path]:
    candidate = Path(project).expanduser().resolve()
    if candidate.is_file():
        if candidate.suffix.lower() != ".uproject":
            raise InstallError(f"expected a .uproject file, got: {candidate}")
        return candidate, candidate.parent

    if not candidate.is_dir():
        raise InstallError(f"project path does not exist: {candidate}")

    project_files = sorted(candidate.glob("*.uproject"))
    if not project_files:
        raise InstallError(f"no .uproject file found in: {candidate}")
    if len(project_files) > 1:
        names = ", ".join(path.name for path in project_files)
        raise InstallError(f"multiple .uproject files found in {candidate}: {names}")
    return project_files[0], candidate


def _package_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in _package_files(root):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        data = path.read_bytes()
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def install_into_project(
    project: str | Path,
    *,
    replace: bool = False,
    source: str | Path | None = None,
) -> dict[str, object]:
    """Copy this package into ``Content/Python`` and return an install receipt."""
    project_file, project_root = _resolve_project(project)
    source_root = (
        Path(source).expanduser().resolve()
        if source is not None
        else Path(__file__).parent.resolve()
    )
    if not source_root.is_dir() or not (source_root / "__init__.py").is_file():
        raise InstallError(f"package source is invalid: {source_root}")

    python_root = project_root / "Content" / "Python"
    destination = python_root / "ue5_scene_kit"
    python_root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".ue5-scene-kit-", dir=python_root))
    backup = python_root / ".ue5-scene-kit-backup"

    try:
        shutil.copytree(
            source_root,
            staging,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        source_digest = _tree_digest(staging)

        if destination.exists() and _tree_digest(destination) == source_digest:
            return _receipt("unchanged", project_file, destination, staging, source_digest)

        if destination.exists() and not replace:
            raise InstallError(
                f"installation already exists with different content: {destination}; "
                "rerun with --replace to update it"
            )

        status = "installed"
        if destination.exists():
            if backup.exists():
                raise InstallError(f"stale installer backup must be removed manually: {backup}")
            destination.rename(backup)
            status = "replaced"

        try:
            staging.rename(destination)
        except Exception:
            if backup.exists() and not destination.exists():
                backup.rename(destination)
            raise
        if backup.exists():
            shutil.rmtree(backup)

        return _receipt(status, project_file, destination, destination, source_digest)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def _receipt(
    status: str,
    project_file: Path,
    destination: Path,
    installed_root: Path,
    digest: str,
) -> dict[str, object]:
    return {
        "status": status,
        "project": str(project_file),
        "destination": str(destination),
        "files": len(_package_files(installed_root)),
        "sha256": digest,
    }
