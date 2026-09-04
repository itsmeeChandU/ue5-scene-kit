"""Offline discovery and validation CLI."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from . import __version__
from .atmosphere import resolve_atmosphere
from .install import InstallError, install_into_project
from .presets import ATMOSPHERES, LENSES, WINDS, list_presets


def _validate() -> dict[str, int]:
    for name in ATMOSPHERES:
        resolve_atmosphere(name)
    for spec in LENSES.values():
        spec.validate()
    for spec in WINDS.values():
        spec.validate()
    return {"atmospheres": len(ATMOSPHERES), "lenses": len(LENSES), "winds": len(WINDS)}


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="ue5-scene-kit")
    parser.add_argument(
        "command",
        choices=("list", "validate", "install"),
        nargs="?",
        default="list",
    )
    parser.add_argument("--project", help=".uproject file or directory for the install command")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="replace a changed Content/Python installation",
    )
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args(argv)
    if args.command == "install":
        if not args.project:
            parser.error("install requires --project")
        try:
            result = install_into_project(args.project, replace=args.replace)
        except InstallError as exc:
            print(f"ue5-scene-kit: {exc}", file=sys.stderr)
            return 2
    else:
        result = list_presets() if args.command == "list" else _validate()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
