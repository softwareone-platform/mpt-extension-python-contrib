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


def scaffold(module: str) -> Path:
    """Render the module template and copy the repository LICENSE into it."""
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
    return module_dir


def main() -> int:
    """Render a module scaffold from the command line."""
    parser = argparse.ArgumentParser(description="Scaffold a contrib module.")
    parser.add_argument("--module", required=True, help="kebab-case module name")
    args = parser.parse_args()

    module_dir = scaffold(args.module)
    sys.stdout.write(f"Created {module_dir.relative_to(ROOT)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
