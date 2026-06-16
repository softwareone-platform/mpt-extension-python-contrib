"""Scaffold one independently released contrib module from the copier template."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

from copier import run_copy

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates" / "module"
MODULE_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


def is_valid_module(module: str) -> bool:
    """Return whether the module name is lowercase kebab-case."""
    return MODULE_PATTERN.fullmatch(module) is not None


def python_name(module: str) -> str:
    """Return the Python import segment for a repository module."""
    return module.replace("-", "_")


def render_insert(source_text: str, anchor: str, addition: str) -> str:
    """Return text with the addition inserted after the first anchor occurrence."""
    if anchor not in source_text:
        raise ValueError(f"anchor not found: {anchor!r}")
    return source_text.replace(anchor, f"{anchor}{addition}", 1)


def wiring_edits(module: str) -> list[tuple[Path, str, str]]:
    """Return the (file, anchor, addition) edits that register one module."""
    import_name = python_name(module)
    distribution = f"mpt-extension-contrib-{module}"
    pyproject = ROOT / "pyproject.toml"
    shared_row = (
        "| `shared/` | `mpt-extension-contrib-shared` | `mpt_extension_contrib.shared` | internal |"
    )
    contrib = "mpt_extension_contrib"
    return [
        (pyproject, '[tool.uv.workspace]\nmembers = [\n  "shared",', f'\n  "{module}",'),
        (pyproject, '  "shared/tests",', f'\n  "{module}/tests",'),
        (pyproject, 'mypy_path = [\n  "shared",', f'\n  "{module}",'),
        (ROOT / "make" / "common.mk", "PACKAGES := shared", f" {module}"),
        (
            ROOT / "README.md",
            shared_row,
            f"\n| `{module}/` | `{distribution}` | `{contrib}.{import_name}` | public |",
        ),
        (
            ROOT / "AGENTS.md",
            "(distribution `mpt-extension-contrib-shared`).",
            (
                f"\n- [`{module}/`]({module}): public package exposed as "
                f"`{contrib}.{import_name}` (distribution `{distribution}`)."
            ),
        ),
    ]


def wire(module: str) -> None:
    """Register the module across the workspace tooling and docs atomically.

    Every anchor is rendered in memory first, so a missing anchor raises before
    any file is written and the repository is never left partially wired.
    """
    rendered: dict[Path, str] = {}
    for path, anchor, addition in wiring_edits(module):
        rendered[path] = render_insert(
            rendered.get(path, path.read_text(encoding="utf-8")), anchor, addition
        )
    for path, text in rendered.items():
        path.write_text(text, encoding="utf-8")


def scaffold(module: str) -> Path:
    """Render the module template, copy the LICENSE, and wire it into the workspace."""
    if not is_valid_module(module):
        raise ValueError("module must use lowercase kebab-case, e.g. payment-terms")
    module_dir = ROOT / module
    if module_dir.exists():
        raise ValueError(f"{module}: module directory already exists")

    run_copy(
        str(TEMPLATE_DIR),
        str(module_dir),
        data={"module": module},
        defaults=True,
        quiet=True,
    )
    shutil.copyfile(ROOT / "LICENSE", module_dir / "LICENSE")
    wire(module)
    return module_dir


def main() -> int:
    """Render a module scaffold from the command line."""
    parser = argparse.ArgumentParser(description="Scaffold a contrib module.")
    parser.add_argument("--module", required=True, help="kebab-case module name")
    args = parser.parse_args()

    module_dir = scaffold(args.module)
    sys.stdout.write(f"Created and wired {module_dir.relative_to(ROOT)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
