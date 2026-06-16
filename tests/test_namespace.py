import importlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

PACKAGE_MODULES = (
    "mpt_extension_contrib.shared",
    "mpt_extension_contrib.due_date",
)


def test_namespace_has_no_root_init() -> None:
    result = sorted(
        path
        for path in REPO_ROOT.rglob("mpt_extension_contrib/__init__.py")
        if ".venv" not in path.parts
    )

    assert result == []


def test_namespace_is_pep420_package() -> None:
    result = importlib.import_module("mpt_extension_contrib")

    assert getattr(result, "__file__", None) is None
    assert len(list(result.__path__)) >= 2


def test_distributions_coexist_without_shadowing() -> None:
    result = frozenset(
        Path(importlib.import_module(name).__file__).parent for name in PACKAGE_MODULES
    )

    assert len(result) == len(PACKAGE_MODULES)
