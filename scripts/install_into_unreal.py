"""Install UE5 Scene Kit from a source checkout into an Unreal project."""
# ruff: noqa: E402, I001
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ue5_scene_kit.__main__ import main


if __name__ == "__main__":
    raise SystemExit(main(["install", *sys.argv[1:]]))
