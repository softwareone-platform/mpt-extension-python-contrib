from dataclasses import dataclass

import pytest


@dataclass(frozen=True)
class FakeSettings:
    """Settings double exposing the fields the built-in channels read."""

    teams_webhook_url: str | None = None
    teams_notifications_enabled: bool = False


@pytest.fixture
def teams_settings():
    return FakeSettings(
        teams_webhook_url="https://example.com/workflows/webhook",
        teams_notifications_enabled=True,
    )


@pytest.fixture
def empty_settings():
    return FakeSettings()


@pytest.fixture
def insecure_teams_settings():
    return FakeSettings(teams_webhook_url="http://example.com/workflows/webhook")
