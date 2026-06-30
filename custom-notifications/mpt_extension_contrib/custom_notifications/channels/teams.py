"""Teams channel: send Adaptive Cards through a Power Automate Workflows webhook.

This module imports its optional dependencies (``microsoft-teams-cards`` and
``httpx``) at module level, so it is importable only when the ``teams`` extra is
installed. Channel discovery loads it lazily and skips it on ``ImportError``,
which keeps the extra optional for consumers that do not use Teams.
"""

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

import httpx
from microsoft_teams.cards import (
    Action,
    AdaptiveCard,
    CardElement,
    Fact,
    FactSet,
    OpenUrlAction,
    TextBlock,
)
from mpt_extension_contrib.custom_notifications.base import NotificationChannel

logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT = 10.0
_ADAPTIVE_CARD_CONTENT_TYPE = "application/vnd.microsoft.card.adaptive"

_Color = Literal["Good", "Warning", "Attention", "Accent"]
_Severity = tuple[str, _Color]

_WARNING: _Severity = ("☢", "Warning")
_SUCCESS: _Severity = ("✅", "Good")
_ERROR: _Severity = ("💣", "Attention")
_EXCEPTION: _Severity = ("🔥", "Attention")


@dataclass(frozen=True)
class Button:
    """A link button rendered as an ``Action.OpenUrl`` on the card."""

    label: str
    url: str


@dataclass(frozen=True)
class FactsSection:
    """A titled key/value section rendered as a ``FactSet`` on the card."""

    title: str
    entries: Mapping[str, str]


class TeamsSettings(Protocol):
    """Settings the Teams channel reads from."""

    teams_webhook_url: str | None


@runtime_checkable
class TeamsNotifier(Protocol):
    """Contract a custom Teams implementation must preserve."""

    def send_warning(
        self,
        title: str,
        text: str,
        *,
        button: Button | None = None,
        facts: FactsSection | None = None,
    ) -> None:
        """Send a warning-severity notification."""

    def send_success(
        self,
        title: str,
        text: str,
        *,
        button: Button | None = None,
        facts: FactsSection | None = None,
    ) -> None:
        """Send a success-severity notification."""

    def send_error(
        self,
        title: str,
        text: str,
        *,
        button: Button | None = None,
        facts: FactsSection | None = None,
    ) -> None:
        """Send an error-severity notification."""

    def send_exception(
        self,
        title: str,
        text: str,
        *,
        button: Button | None = None,
        facts: FactsSection | None = None,
    ) -> None:
        """Send an exception-severity notification."""

    def send_card(self, card: AdaptiveCard) -> None:
        """Send an already-built Adaptive Card."""


def _facts_blocks(section: FactsSection) -> list[CardElement]:
    """Render a facts section as a heading plus a ``FactSet``."""
    facts: list[Fact] = []
    for name, detail in section.entries.items():
        facts.append(Fact(title=name, value=detail))
    heading = TextBlock(text=section.title, weight="Bolder", wrap=True)
    return [heading, FactSet(facts=facts)]


class TeamsNotifications:
    """Send Adaptive Cards to a Teams channel via a Workflows webhook."""

    def __init__(self, *, webhook_url: str) -> None:
        self._webhook_url = webhook_url

    def send_warning(
        self,
        title: str,
        text: str,
        *,
        button: Button | None = None,
        facts: FactsSection | None = None,
    ) -> None:
        """Post a warning-styled Adaptive Card."""
        self.send_card(self._card(title, text, _WARNING, button=button, facts=facts))

    def send_success(
        self,
        title: str,
        text: str,
        *,
        button: Button | None = None,
        facts: FactsSection | None = None,
    ) -> None:
        """Post a success-styled Adaptive Card."""
        self.send_card(self._card(title, text, _SUCCESS, button=button, facts=facts))

    def send_error(
        self,
        title: str,
        text: str,
        *,
        button: Button | None = None,
        facts: FactsSection | None = None,
    ) -> None:
        """Post an error-styled Adaptive Card."""
        self.send_card(self._card(title, text, _ERROR, button=button, facts=facts))

    def send_exception(
        self,
        title: str,
        text: str,
        *,
        button: Button | None = None,
        facts: FactsSection | None = None,
    ) -> None:
        """Post an exception-styled Adaptive Card."""
        self.send_card(self._card(title, text, _EXCEPTION, button=button, facts=facts))

    def send_card(self, card: AdaptiveCard) -> None:
        """Post an already-built Adaptive Card; webhook errors are logged, not raised."""
        payload = {
            "type": "message",
            "attachments": [
                {
                    "contentType": _ADAPTIVE_CARD_CONTENT_TYPE,
                    "content": card.model_dump(by_alias=True, exclude_none=True),
                },
            ],
        }
        try:
            httpx.post(self._webhook_url, json=payload, timeout=_REQUEST_TIMEOUT).raise_for_status()
        except httpx.HTTPError:
            logger.exception("Failed to send Teams notification")

    def _card(
        self,
        title: str,
        text: str,
        severity: _Severity,
        *,
        button: Button | None,
        facts: FactsSection | None,
    ) -> AdaptiveCard:
        emoji, color = severity
        heading = f"{emoji} {title}"
        body: list[CardElement] = [
            TextBlock(text=heading, weight="Bolder", size="Large", color=color, wrap=True),
            TextBlock(text=text, wrap=True),
        ]
        if facts is not None:
            body += _facts_blocks(facts)
        actions: list[Action] = []
        if button is not None:
            actions.append(OpenUrlAction(title=button.label, url=button.url))
        return AdaptiveCard(body=body, actions=actions)


def _build(settings: TeamsSettings) -> TeamsNotifications | None:
    """Build the Teams channel from settings, or ``None`` when unconfigured.

    Raises:
        ValueError: When the configured webhook URL is not HTTPS.
    """
    webhook_url = settings.teams_webhook_url
    if not webhook_url:
        return None
    if not webhook_url.startswith("https://"):
        raise ValueError("teams_webhook_url must be an https:// URL")
    return TeamsNotifications(webhook_url=webhook_url)


channel: NotificationChannel[TeamsSettings] = NotificationChannel(name="teams", build=_build)
"""Entry-point descriptor discovered by :func:`build_registry`."""
