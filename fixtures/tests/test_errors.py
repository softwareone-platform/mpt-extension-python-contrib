from mpt_extension_contrib.fixtures import mpt_error_factory


def test_error_has_core_fields() -> None:
    result = mpt_error_factory(400, "Bad Request", "Invalid order")

    assert result["status"] == 400
    assert result["title"] == "Bad Request"
    assert result["detail"] == "Invalid order"


def test_error_omits_errors_when_absent() -> None:
    result = mpt_error_factory(400, "Bad Request", "Invalid order")

    assert "errors" not in result


def test_error_includes_field_errors_when_given() -> None:
    result = mpt_error_factory(400, "Bad Request", "x", field_errors={"name": ["required"]})

    assert result["errors"] == {"name": ["required"]}
