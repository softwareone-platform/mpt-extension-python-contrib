"""Teams channel: send Adaptive Cards through a Power Automate Workflows webhook.

This module imports its optional dependencies (``microsoft-teams-cards`` and
``httpx``) at module level, so it is importable only when the ``teams`` extra is
installed. Channel discovery loads it lazily and skips it on ``ImportError``,
which keeps the extra optional for consumers that do not use Teams.

Card construction lives in :mod:`.teams_cards`; the async counterpart is
:mod:`.teams_async`.
"""

import logging
from typing import override

import httpx
from microsoft_teams.cards import AdaptiveCard
from mpt_extension_contrib.custom_notifications.base import Notification, NotificationChannel
from mpt_extension_contrib.custom_notifications.channels.teams_cards import (
    Button,
    FactsSection,
    TeamsSettings,
    payload,
    severity_card,
)

logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT = 10.0
_DISABLED_LOG = "Teams notifications are disabled; skipping send"
_FAILED_LOG = "Failed to send Teams notification"


class TeamsNotifier(Notification):
    """Base class a custom Teams implementation subclasses.

    Concrete channels override every method; the registry resolves a channel by
    the notifier base class it inherits (see :meth:`NotificationRegistry.get`).
    """

    def send_warning(
        self,
        title: str,
        text: str,
        *,
        button: Button | None = None,
        facts: FactsSection | None = None,
    ) -> None:
        """Send a warning-severity notification."""
        raise NotImplementedError

    def send_success(
        self,
        title: str,
        text: str,
        *,
        button: Button | None = None,
        facts: FactsSection | None = None,
    ) -> None:
        """Send a success-severity notification."""
        raise NotImplementedError

    def send_error(
        self,
        title: str,
        text: str,
        *,
        button: Button | None = None,
        facts: FactsSection | None = None,
    ) -> None:
        """Send an error-severity notification."""
        raise NotImplementedError

    def send_exception(
        self,
        title: str,
        text: str,
        *,
        button: Button | None = None,
        facts: FactsSection | None = None,
    ) -> None:
        """Send an exception-severity notification."""
        raise NotImplementedError

    def send_card(self, card: AdaptiveCard) -> None:
        """Send an already-built Adaptive Card."""
        raise NotImplementedError


class TeamsNotifications(TeamsNotifier):
    """Send Adaptive Cards to a Teams channel via a Workflows webhook."""

    def __init__(self, *, webhook_url: str, enabled: bool) -> None:
        self._webhook_url = webhook_url
        self._enabled = enabled

    @override
    def send_warning(
        self,
        title: str,
        text: str,
        *,
        button: Button | None = None,
        facts: FactsSection | None = None,
    ) -> None:
        """Post a warning-styled Adaptive Card."""
        self.send_card(severity_card(title, text, "warning", button=button, facts=facts))

    @override
    def send_success(
        self,
        title: str,
        text: str,
        *,
        button: Button | None = None,
        facts: FactsSection | None = None,
    ) -> None:
        """Post a success-styled Adaptive Card."""
        self.send_card(severity_card(title, text, "success", button=button, facts=facts))

    @override
    def send_error(
        self,
        title: str,
        text: str,
        *,
        button: Button | None = None,
        facts: FactsSection | None = None,
    ) -> None:
        """Post an error-styled Adaptive Card."""
        self.send_card(severity_card(title, text, "error", button=button, facts=facts))

    @override
    def send_exception(
        self,
        title: str,
        text: str,
        *,
        button: Button | None = None,
        facts: FactsSection | None = None,
    ) -> None:
        """Post an exception-styled Adaptive Card."""
        self.send_card(severity_card(title, text, "exception", button=button, facts=facts))

    @override
    def send_card(self, card: AdaptiveCard) -> None:
        """Post an already-built Adaptive Card; webhook errors are logged, not raised.

        A no-op when the channel is disabled.
        """
        if not self._enabled:
            logger.info(_DISABLED_LOG)
            return
        try:
            httpx.post(
                self._webhook_url,
                json=payload(card),
                timeout=_REQUEST_TIMEOUT,
            ).raise_for_status()
        except httpx.HTTPError:
            logger.exception(_FAILED_LOG)


def resolve_config(settings: TeamsSettings) -> str | None:
    """Return the validated webhook URL when Teams is enabled, else ``None``.

    Shared by the sync and async Teams channels (the async one imports it). The
    enable flag is the master switch: a disabled channel is skipped, while an
    enabled one must be fully configured.

    Raises:
        ValueError: When enabled but ``teams_webhook_url`` is missing or not HTTPS.
    """
    # Read defensively: build_registry builds every channel from one settings
    # object, so settings that do not target Teams must not raise here. When the
    # enable flag is absent (settings predating it), fall back to "enabled if a
    # webhook is set" to preserve the previous behaviour.
    webhook_url: str | None = getattr(settings, "teams_webhook_url", None)
    if not getattr(settings, "teams_notifications_enabled", webhook_url is not None):
        return None
    if not webhook_url:
        raise ValueError("Teams notifications are enabled but teams_webhook_url is not set")
    if not webhook_url.startswith("https://"):
        raise ValueError("teams_webhook_url must be an https:// URL")
    return webhook_url


def _build(settings: TeamsSettings) -> TeamsNotifications | None:
    """Build the Teams channel from settings, or ``None`` when disabled."""
    webhook_url = resolve_config(settings)
    if webhook_url is None:
        return None
    return TeamsNotifications(webhook_url=webhook_url, enabled=True)


channel: NotificationChannel[TeamsSettings] = NotificationChannel(name="teams", build=_build)
