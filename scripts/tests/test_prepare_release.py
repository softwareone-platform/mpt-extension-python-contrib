import pytest

from scripts.prepare_release import parse_pair, release_matrix

MEMBERS = ("shared", "due-date")


def test_parse_pair_splits_module_and_version() -> None:
    result = parse_pair("due-date=2.0.1")

    assert result == ("due-date", "2.0.1")


@pytest.mark.parametrize("token", ["due-date", "due-date=2.0", "due-date=v1.0.0", "=1.0.0"])
def test_parse_pair_rejects_bad_tokens(token: str) -> None:
    with pytest.raises(ValueError, match="expected <module>"):
        parse_pair(token)


def test_release_matrix_multi_component() -> None:
    result = release_matrix("due-date=2.0.1,shared=1.2.0", MEMBERS)

    assert result == [
        {
            "package": "shared",
            "distribution": "mpt-extension-contrib-shared",
            "version": "1.2.0",
            "tag": "shared-1.2.0",
        },
        {
            "package": "due-date",
            "distribution": "mpt-extension-contrib-due-date",
            "version": "2.0.1",
            "tag": "due-date-2.0.1",
        },
    ]


def test_release_matrix_rejects_unknown_package() -> None:
    with pytest.raises(ValueError, match="unknown packages: ghost"):
        release_matrix("ghost=1.0.0", MEMBERS)


def test_release_matrix_rejects_duplicates() -> None:
    with pytest.raises(ValueError, match="duplicates"):
        release_matrix("shared=1.0.0,shared=1.0.1", MEMBERS)
