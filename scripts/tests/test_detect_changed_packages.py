from scripts.detect_changed_packages import (
    affected_packages,
    impacts_all_packages,
    package_matrix,
    sonar_secret_name,
    workspace_members,
)


def test_module_change_selects_only_that_module() -> None:
    result = affected_packages(["due-date/mpt_extension_contrib/due_date/calculation.py"])

    assert result == ["due-date"]


def test_tooling_change_selects_all_members() -> None:
    result = affected_packages(["uv.lock"])

    assert result == workspace_members()


def test_unrelated_change_selects_nothing() -> None:
    result = affected_packages(["LICENSE"])

    assert result == []


def test_global_path_impacts_all() -> None:
    result = impacts_all_packages("scripts/check_repository.py")

    assert result is True


def test_module_path_not_global() -> None:
    result = impacts_all_packages("shared/pyproject.toml")

    assert result is False


def test_filename_prefix_is_not_global() -> None:
    result = impacts_all_packages("pyproject.toml.bak")

    assert result is False


def test_sonar_secret_name() -> None:
    result = sonar_secret_name("order-status-utils")

    assert result == "SONAR_TOKEN_ORDER_STATUS_UTILS"


def test_package_matrix_carries_name_and_secret() -> None:
    result = package_matrix(["due-date/x.py"])

    assert result == [{"name": "due-date", "sonar_secret": "SONAR_TOKEN_DUE_DATE"}]
