from mpt_extension_contrib.due_date import normalize_example


def test_normalize_example() -> None:
    result = normalize_example("  Example Value  ")

    assert result == "example value"
