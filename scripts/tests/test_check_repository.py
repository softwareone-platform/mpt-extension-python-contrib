from pathlib import Path

import pytest

from scripts.check_repository import (
    load_toml,
    main,
    validate_files,
    validate_package,
    validate_root,
)

PY_TYPED_ERROR = "foo: missing mpt_extension_contrib/foo/py.typed (PEP 561)"


def _make_package(package_dir: Path, *, py_typed: bool) -> None:
    import_root = package_dir / "mpt_extension_contrib" / "foo"
    import_root.mkdir(parents=True)
    (import_root / "__init__.py").write_text("")
    if py_typed:
        (import_root / "py.typed").write_text("")


def test_repository_structure_is_valid() -> None:
    result = main()

    assert result == 0


def test_validate_root_returns_members() -> None:
    result = validate_root()

    assert result[0] == []
    assert "shared" in result[1]


def test_validate_package_reports_missing_member() -> None:
    result = validate_package("does-not-exist")

    assert result == ["does-not-exist: workspace member directory is missing"]


def test_load_toml_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="cannot read TOML"):
        load_toml(tmp_path / "missing.toml")


def test_files_report_missing_py_typed(tmp_path: Path) -> None:
    _make_package(tmp_path, py_typed=False)

    result = validate_files("foo", tmp_path)

    assert PY_TYPED_ERROR in result


def test_files_accept_py_typed(tmp_path: Path) -> None:
    _make_package(tmp_path, py_typed=True)

    result = validate_files("foo", tmp_path)

    assert PY_TYPED_ERROR not in result
