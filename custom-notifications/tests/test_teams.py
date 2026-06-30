import json
from dataclasses import dataclass

import httpx
import pytest
from mpt_extension_contrib.custom_notifications import build_registry
from mpt_extension_contrib.custom_notifications.channels.teams import (
    Button,
    FactsSection,
    TeamsNotifications,
    TeamsNotifier,
)


@dataclass(frozen=True)
class _LegacySettings:
    teams_webhook_url: str = "https://example.com/webhook"


_WEBHOOK = "https://example.com/webhook"
_ADAPTIVE_CARD_CONTENT_TYPE = "application/vnd.microsoft.card.adaptive"


@pytest.fixture
def notifier():
    return TeamsNotifications(webhook_url=_WEBHOOK, enabled=True)


@pytest.fixture
def teams_route(respx_mock):
    return respx_mock.post(_WEBHOOK).mock(return_value=httpx.Response(200))


@pytest.fixture
def failing_route(respx_mock):
    return respx_mock.post(_WEBHOOK).mock(return_value=httpx.Response(500))


@pytest.fixture
def unreachable_route(respx_mock):
    return respx_mock.post(_WEBHOOK).mock(side_effect=httpx.ConnectError("down"))


@pytest.fixture
def post_notification(notifier, teams_route):
    def factory(method, **kwargs):
        getattr(notifier, method)("Title", "Body", **kwargs)
        return json.loads(teams_route.calls.last.request.content)

    return factory


@pytest.fixture
def post_card(post_notification):
    def factory(method, **kwargs):
        payload = post_notification(method, **kwargs)
        return payload["attachments"][0]["content"]

    return factory


@pytest.mark.parametrize(
    ("method", "emoji", "color"),
    [
        ("send_warning", "☢", "Warning"),
        ("send_success", "✅", "Good"),
        ("send_error", "💣", "Attention"),
        ("send_exception", "🔥", "Attention"),
    ],
)
def test_severity_styling(post_card, method, emoji, color):
    result = post_card(method)

    assert result["body"][0]["text"] == f"{emoji} Title"
    assert result["body"][0]["color"] == color


def test_envelope_shape(post_notification):
    result = post_notification("send_error")

    assert result["type"] == "message"
    assert result["attachments"][0]["contentType"] == _ADAPTIVE_CARD_CONTENT_TYPE


def test_button_and_facts(post_card):
    button = Button(label="Open", url="https://example.com/o")
    facts = FactsSection(title="Details", entries={"Order": "ORD-1"})
    expected_facts = [{"title": "Order", "value": "ORD-1"}]

    result = post_card("send_error", button=button, facts=facts)

    assert result["body"][3]["facts"] == expected_facts
    assert result["actions"][0]["url"] == "https://example.com/o"


def test_webhook_error_swallowed(notifier, failing_route):
    result = notifier.send_error("Title", "Body")

    assert result is None


def test_request_error_swallowed(notifier, unreachable_route):
    result = notifier.send_error("Title", "Body")

    assert result is None


def test_disabled_skips_post(respx_mock):
    notifier = TeamsNotifications(webhook_url=_WEBHOOK, enabled=False)

    notifier.send_error("Title", "Body")  # act

    assert not respx_mock.calls


def test_legacy_settings_stay_enabled(respx_mock):
    route = respx_mock.post(_WEBHOOK).mock(return_value=httpx.Response(200))
    registry = build_registry(_LegacySettings())

    registry.get(TeamsNotifier).send_error("Title", "Body")  # act

    assert route.called
