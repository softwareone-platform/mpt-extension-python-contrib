"""Validate the contrib monorepo package structure and metadata."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_PACKAGE_FILES = (
    "AGENTS.md",
    "LICENSE",
    "README.md",
    "docs",
    "pyproject.toml",
    "sonar-project.properties",
    "tests",
)
REQUIRED_PACKAGE_DOCS = (
    "architecture.md",
    "contributing.md",
    "releases.md",
    "testing.md",
)


def load_toml(path: Path) -> dict[str, Any]:
    """Load a TOML document, raising ValueError on a read or parse failure."""
    try:
        with path.open("rb") as stream:
            return tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"{path.name}: cannot read TOML ({exc})") from exc


def workspace_members(pyproject: dict[str, Any]) -> list[str]:
    """Return the declared workspace members as a list of strings."""
    tool = pyproject.get("tool", {})
    uv_config = tool.get("uv", {})
    members = uv_config.get("workspace", {}).get("members", [])
    if not isinstance(members, list):
        return []
    return [name for name in members if isinstance(name, str)]


def validate_root() -> tuple[list[str], list[str]]:
    """Validate root workspace metadata; return (errors, declared members)."""
    errors: list[str] = []
    if not (ROOT / "LICENSE").is_file():
        errors.append("root LICENSE is missing")
    try:
        pyproject = load_toml(ROOT / "pyproject.toml")
    except ValueError as exc:
        errors.append(str(exc))
        return errors, []

    if "project" in pyproject:
        errors.append("root pyproject.toml must not define [project]")

    members = workspace_members(pyproject)
    if not members:
        errors.append("root pyproject.toml must define non-empty [tool.uv.workspace].members")
    return errors, members


def validate_files(member: str, package_dir: Path) -> list[str]:
    """Return errors for missing required files and docs in one package."""
    errors = [
        f"{member}: missing {required_file}"
        for required_file in REQUIRED_PACKAGE_FILES
        if not (package_dir / required_file).exists()
    ]
    errors.extend(
        f"{member}: missing docs/{required_doc}"
        for required_doc in REQUIRED_PACKAGE_DOCS
        if not (package_dir / "docs" / required_doc).is_file()
    )
    return errors


def validate_metadata(member: str, package_dir: Path) -> list[str]:
    """Return errors for one package's pyproject metadata and namespace layout."""
    expected_distribution = f"mpt-extension-contrib-{member}"
    import_name = member.replace("-", "_")
    errors: list[str] = []

    if (package_dir / "mpt_extension_contrib" / "__init__.py").is_file():
        errors.append(f"{member}: mpt_extension_contrib/__init__.py must not exist (PEP 420)")
    try:
        project = load_toml(package_dir / "pyproject.toml").get("project", {})
    except ValueError as exc:
        errors.append(f"{member}: {exc}")
        return errors

    if project.get("name") != expected_distribution:
        errors.append(
            f"{member}/pyproject.toml: project.name must be {expected_distribution!r}, "
            f"got {project.get('name')!r}",
        )
    if project.get("version") != "0.0.0":
        errors.append(f"{member}/pyproject.toml: project.version must be the 0.0.0 placeholder")
    if not (package_dir / "mpt_extension_contrib" / import_name / "__init__.py").is_file():
        errors.append(f"{member}: missing mpt_extension_contrib/{import_name}/__init__.py")
    return errors


def validate_package(member: str) -> list[str]:
    """Return all structural errors for one workspace member."""
    package_dir = ROOT / member
    if not package_dir.is_dir():
        return [f"{member}: workspace member directory is missing"]

    errors = validate_files(member, package_dir)
    if (package_dir / "pyproject.toml").is_file():
        errors.extend(validate_metadata(member, package_dir))
    return errors


def main() -> int:
    """Run repository structure validation."""
    errors, members = validate_root()
    for member in members:
        errors.extend(validate_package(member))

    if errors:
        sys.stderr.write("Repository structure validation failed:\n")
        for error in errors:
            sys.stderr.write(f"- {error}\n")
        return 1

    sys.stdout.write(f"Repository structure validation passed for {len(members)} packages.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
