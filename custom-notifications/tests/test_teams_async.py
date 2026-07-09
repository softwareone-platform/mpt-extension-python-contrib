import json

import httpx
import pytest
from mpt_extension_contrib.custom_notifications import build_registry
from mpt_extension_contrib.custom_notifications.channels.teams_async import (
    AsyncTeamsNotifications,
    AsyncTeamsNotifier,
)
from mpt_extension_contrib.custom_notifications.channels.teams_async import (
    channel as async_teams_channel,
)
from mpt_extension_contrib.custom_notifications.channels.teams_cards import Button, FactsSection

_WEBHOOK = "https://example.com/webhook"


@pytest.fixture
def notifier():
    return AsyncTeamsNotifications(webhook_url=_WEBHOOK, enabled=True)


@pytest.fixture
def teams_route(respx_mock):
    return respx_mock.post(_WEBHOOK).mock(return_value=httpx.Response(200))


@pytest.fixture
def failing_route(respx_mock):
    return respx_mock.post(_WEBHOOK).mock(return_value=httpx.Response(500))


@pytest.fixture
def post_card(notifier, teams_route):
    async def factory(method, **kwargs):
        await getattr(notifier, method)("Title", "Body", **kwargs)
        payload = json.loads(teams_route.calls.last.request.content)
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
async def test_severity_styling(post_card, method, emoji, color):
    result = await post_card(method)

    assert result["body"][0]["text"] == f"{emoji} Title"
    assert result["body"][0]["color"] == color


async def test_button_and_facts(post_card):
    button = Button(label="Open", url="https://example.com/o")
    facts = FactsSection(title="Details", entries={"Order": "ORD-1"})
    expected_facts = [{"title": "Order", "value": "ORD-1"}]

    result = await post_card("send_error", button=button, facts=facts)

    assert result["body"][3]["facts"] == expected_facts
    assert result["actions"][0]["url"] == "https://example.com/o"


async def test_webhook_error_swallowed(notifier, failing_route):
    result = await notifier.send_error("Title", "Body")

    assert result is None


async def test_disabled_skips_post(respx_mock):
    notifier = AsyncTeamsNotifications(webhook_url=_WEBHOOK, enabled=False)

    await notifier.send_error("Title", "Body")  # act

    assert not respx_mock.calls


def test_build_registers_async_teams(teams_settings):
    registry = build_registry(teams_settings)

    result = registry.get(AsyncTeamsNotifier)

    assert result is not None


def test_build_rejects_non_https(insecure_teams_settings):
    with pytest.raises(ValueError, match="https"):
        async_teams_channel.build(insecure_teams_settings)
