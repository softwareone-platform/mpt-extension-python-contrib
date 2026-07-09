from typing import ClassVar

import pytest
import requests
from atlassian.errors import ApiError
from mpt_extension_contrib.reports import ConfluenceClient
from mpt_extension_contrib.reports import confluence as confluence_module


class FakeConfluence:
    instances: ClassVar[list["FakeConfluence"]] = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.calls = []
        self.error = None
        FakeConfluence.instances.append(self)

    def attach_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error


@pytest.fixture
def fake_confluence(monkeypatch):
    FakeConfluence.instances = []
    monkeypatch.setattr(confluence_module, "Confluence", FakeConfluence)
    return FakeConfluence


def test_attach_content_forwards_arguments(fake_confluence):
    client = ConfluenceClient("https://example.atlassian.net", "user", "token")

    result = client.attach_content(
        "page-1", "orders.xlsx", b"data", content_type="application/pdf", comment="Total 3"
    )

    assert result is True
    assert fake_confluence.instances[0].kwargs == {
        "url": "https://example.atlassian.net",
        "username": "user",
        "password": "token",
        "cloud": True,
    }
    assert fake_confluence.instances[0].calls == [
        {
            "content": b"data",
            "name": "orders.xlsx",
            "content_type": "application/pdf",
            "page_id": "page-1",
            "comment": "Total 3",
        },
    ]


def test_attach_content_defaults_comment_to_none(fake_confluence):
    client = ConfluenceClient("https://example.atlassian.net", "user", "token")

    result = client.attach_content("page-1", "orders.xlsx", b"data", content_type="application/pdf")

    assert result is True
    assert fake_confluence.instances[0].calls == [
        {
            "content": b"data",
            "name": "orders.xlsx",
            "content_type": "application/pdf",
            "page_id": "page-1",
            "comment": None,
        },
    ]


@pytest.mark.parametrize(
    "error",
    [
        requests.exceptions.HTTPError("boom"),
        ApiError("boom"),
    ],
)
def test_attach_content_returns_false_on_error(fake_confluence, error):
    client = ConfluenceClient("https://example.atlassian.net", "user", "token")
    fake_confluence.instances[0].error = error

    result = client.attach_content("page-1", "orders.xlsx", b"data", content_type="application/pdf")

    assert result is False
