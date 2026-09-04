from __future__ import annotations

import json
from pathlib import Path

import pytest

from ue5_scene_kit.__main__ import main
from ue5_scene_kit.install import InstallError, install_into_project


def _project(tmp_path: Path, name: str = "Demo") -> Path:
    project = tmp_path / name
    project.mkdir()
    project_file = project / f"{name}.uproject"
    project_file.write_text("{}\n", encoding="utf-8")
    return project_file


def _source(tmp_path: Path) -> Path:
    source = tmp_path / "package"
    source.mkdir()
    (source / "__init__.py").write_text('VALUE = "one"\n', encoding="utf-8")
    (source / "module.py").write_text("ANSWER = 42\n", encoding="utf-8")
    cache = source / "__pycache__"
    cache.mkdir()
    (cache / "module.pyc").write_bytes(b"compiled")
    return source


def test_install_accepts_uproject_file_and_excludes_cache(tmp_path: Path) -> None:
    project_file = _project(tmp_path)
    receipt = install_into_project(project_file, source=_source(tmp_path))

    destination = project_file.parent / "Content" / "Python" / "ue5_scene_kit"
    assert receipt["status"] == "installed"
    assert receipt["files"] == 2
    assert (destination / "module.py").is_file()
    assert not (destination / "__pycache__").exists()


def test_install_accepts_project_directory_and_is_idempotent(tmp_path: Path) -> None:
    project_file = _project(tmp_path)
    source = _source(tmp_path)

    first = install_into_project(project_file.parent, source=source)
    second = install_into_project(project_file.parent, source=source)

    assert first["status"] == "installed"
    assert second["status"] == "unchanged"
    assert first["sha256"] == second["sha256"]


def test_changed_install_requires_replace(tmp_path: Path) -> None:
    project_file = _project(tmp_path)
    source = _source(tmp_path)
    install_into_project(project_file, source=source)
    (source / "module.py").write_text("ANSWER = 43\n", encoding="utf-8")

    with pytest.raises(InstallError, match="--replace"):
        install_into_project(project_file, source=source)

    destination = project_file.parent / "Content" / "Python" / "ue5_scene_kit"
    assert (destination / "module.py").read_text(encoding="utf-8") == "ANSWER = 42\n"


def test_replace_updates_changed_install(tmp_path: Path) -> None:
    project_file = _project(tmp_path)
    source = _source(tmp_path)
    install_into_project(project_file, source=source)
    (source / "module.py").write_text("ANSWER = 43\n", encoding="utf-8")

    receipt = install_into_project(project_file, source=source, replace=True)

    destination = project_file.parent / "Content" / "Python" / "ue5_scene_kit"
    assert receipt["status"] == "replaced"
    assert (destination / "module.py").read_text(encoding="utf-8") == "ANSWER = 43\n"
    assert not (destination.parent / ".ue5-scene-kit-backup").exists()


@pytest.mark.parametrize("value", ["missing", "not-a-project.txt"])
def test_invalid_project_paths_fail(tmp_path: Path, value: str) -> None:
    candidate = tmp_path / value
    if candidate.suffix:
        candidate.write_text("not a project", encoding="utf-8")

    with pytest.raises(InstallError):
        install_into_project(candidate, source=_source(tmp_path))


def test_directory_without_project_fails(tmp_path: Path) -> None:
    source = _source(tmp_path)
    empty = tmp_path / "empty"
    empty.mkdir()

    with pytest.raises(InstallError, match="no .uproject"):
        install_into_project(empty, source=source)


def test_directory_with_multiple_projects_fails(tmp_path: Path) -> None:
    source = _source(tmp_path)
    project = tmp_path / "multi"
    project.mkdir()
    (project / "A.uproject").write_text("{}", encoding="utf-8")
    (project / "B.uproject").write_text("{}", encoding="utf-8")

    with pytest.raises(InstallError, match="multiple .uproject"):
        install_into_project(project, source=source)


def test_cli_install_emits_json_receipt(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    project_file = _project(tmp_path)

    assert main(["install", "--project", str(project_file)]) == 0

    receipt = json.loads(capsys.readouterr().out)
    assert receipt["status"] == "installed"
    assert Path(receipt["destination"]).is_dir()
