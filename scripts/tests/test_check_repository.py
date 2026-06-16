from pathlib import Path

import pytest

from scripts.check_repository import load_toml, main, validate_package, validate_root


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
