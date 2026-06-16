"""Parse a release request into a validated GitHub Actions publish matrix.

Input is a comma-separated list of ``<module>=<version>`` pairs, e.g.
``shared=1.2.0,due-date=2.0.1`` — several components can be released in one run.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tomllib
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parent.parent
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


def workspace_members() -> list[str]:
    """Return the workspace members in their declared order."""
    with (ROOT / "pyproject.toml").open("rb") as stream:
        pyproject: dict[str, Any] = tomllib.load(stream)
    workspace = pyproject["tool"]["uv"]["workspace"]
    return cast("list[str]", workspace["members"])


def parse_pair(token: str) -> tuple[str, str]:
    """Parse one ``<module>=<version>`` token into (module, version)."""
    name, separator, version = token.strip().partition("=")
    if not name or not separator or not VERSION_PATTERN.fullmatch(version):
        raise ValueError(f"{token!r}: expected <module>=<X.Y.Z>")
    return name, version


def release_matrix(selection: str, members: list[str]) -> list[dict[str, str]]:
    """Parse a CSV of ``<module>=<version>`` into validated matrix records."""
    pairs = [parse_pair(token) for token in selection.split(",") if token.strip()]
    if not pairs:
        raise ValueError("provide at least one <module>=<version>")
    chosen = dict(pairs)
    if len(chosen) != len(pairs):
        raise ValueError("packages must not contain duplicates")
    unknown = sorted(set(chosen).difference(members))
    if unknown:
        unknown_list = ", ".join(unknown)
        raise ValueError(f"unknown packages: {unknown_list}")
    return [
        {
            "package": member,
            "distribution": f"mpt-extension-contrib-{member}",
            "version": chosen[member],
            "tag": f"{member}-{chosen[member]}",
        }
        for member in members
        if member in chosen
    ]


def write_github_output(matrix: list[dict[str, str]]) -> None:
    """Expose the release matrix to a GitHub Actions workflow when requested."""
    output_path = os.getenv("GITHUB_OUTPUT")
    if output_path:
        with Path(output_path).open("a", encoding="utf-8") as stream:
            stream.write(f"matrix={json.dumps(matrix)}\n")


def main() -> int:
    """Validate the release request and emit the publish matrix."""
    parser = argparse.ArgumentParser(description="Prepare the release publish matrix.")
    parser.add_argument("--packages", required=True, help="CSV of <module>=<version>")
    args = parser.parse_args()

    matrix = release_matrix(args.packages, workspace_members())
    write_github_output(matrix)
    sys.stdout.write(f"{json.dumps(matrix)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
