import pytest

from scripts.scaffold_module import is_valid_module, python_name, render_insert


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


def test_python_name_converts_hyphens() -> None:
    result = python_name("order-status-utils")

    assert result == "order_status_utils"


def test_render_insert_inserts_once() -> None:
    result = render_insert("members = [\n  shared\n]\n", "  shared", "\n  due_date")

    assert result == "members = [\n  shared\n  due_date\n]\n"


def test_render_insert_raises_on_missing_anchor() -> None:
    with pytest.raises(ValueError, match="anchor not found"):
        render_insert("nothing here", "missing-anchor", "x")
