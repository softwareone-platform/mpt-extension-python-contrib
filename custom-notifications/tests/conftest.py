from dataclasses import dataclass

import pytest


@dataclass(frozen=True)
class FakeSettings:
    """Settings double exposing the fields every built-in channel reads."""

    teams_webhook_url: str | None = None
    teams_notifications_enabled: bool = False
    aws_ses_region: str | None = None
    aws_ses_sender: str | None = None
    aws_ses_access_key: str | None = None
    aws_ses_secret_key: str | None = None
    email_notifications_enabled: bool = False


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
