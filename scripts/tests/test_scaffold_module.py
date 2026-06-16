import pytest

from scripts.scaffold_module import is_valid_module


@pytest.mark.parametrize(
    "module",
    ["payment-terms", "due-date", "shared", "order-status-utils", "a1"],
)
def test_is_valid_module_accepts_kebab_case(module: str) -> None:
    result = is_valid_module(module)

    assert result is True


@pytest.mark.parametrize(
    "module",
    ["Payment-Terms", "payment_terms", "-payment", "payment-", "1payment", "payment terms", ""],
)
def test_is_valid_module_rejects_invalid(module: str) -> None:
    result = is_valid_module(module)

    assert result is False
