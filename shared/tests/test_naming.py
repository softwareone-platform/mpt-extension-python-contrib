from mpt_extension_contrib.shared import normalize_token


def test_normalize_token() -> None:
    result = normalize_token(" Due-Date ")

    assert result == "due_date"
