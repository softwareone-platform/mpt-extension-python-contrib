"""Classify changed repository files into the workspace packages CI must build.

The git diff itself is computed by the CI workflow and passed in via ``--files``;
this script only classifies those paths (module-scoped vs shared tooling), so it
stays pure and side-effect free.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tomllib
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parent.parent

# Shared tooling files: an exact-path change here rebuilds/tests every package.
GLOBAL_FILES = frozenset((
    ".coderabbit.yaml",
    ".dockerignore",
    ".editorconfig",
    ".pre-commit-config.yaml",
    ".python-version",
    "Dockerfile",
    "Makefile",
    "compose.yaml",
    "pyproject.toml",
    "uv.lock",
))
# Shared tooling directories: any change beneath these rebuilds/tests every package.
GLOBAL_DIRS = (".github/", "make/", "scripts/")


def workspace_members() -> list[str]:
    """Return the workspace members in their declared order."""
    with (ROOT / "pyproject.toml").open("rb") as stream:
        pyproject: dict[str, Any] = tomllib.load(stream)
    workspace = pyproject["tool"]["uv"]["workspace"]
    return cast("list[str]", workspace["members"])


def impacts_all_packages(changed_file: str) -> bool:
    """Return whether a changed path affects shared repository tooling."""
    if changed_file in GLOBAL_FILES:
        return True
    return any(changed_file.startswith(global_dir) for global_dir in GLOBAL_DIRS)


def affected_packages(changed_files: list[str]) -> list[str]:
    """Return the workspace members CI must build for the given changed files."""
    members = workspace_members()
    if any(impacts_all_packages(changed_file) for changed_file in changed_files):
        return members
    return [
        member
        for member in members
        if any(changed_file.startswith(f"{member}/") for changed_file in changed_files)
    ]


def write_github_output(packages: list[str]) -> None:
    """Expose the detected packages to a GitHub Actions workflow when requested."""
    output_path = os.getenv("GITHUB_OUTPUT")
    if output_path:
        with Path(output_path).open("a", encoding="utf-8") as stream:
            stream.write(f"packages={json.dumps(packages)}\n")


def main() -> int:
    """Classify the changed files and emit the CI build matrix value."""
    parser = argparse.ArgumentParser(description="Classify changed files into packages.")
    parser.add_argument("--files", nargs="*", default=[], help="changed file paths")
    args = parser.parse_args()

    packages = affected_packages(args.files)
    write_github_output(packages)
    sys.stdout.write(f"{json.dumps(packages)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
