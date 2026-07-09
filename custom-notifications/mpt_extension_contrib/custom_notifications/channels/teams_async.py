"""Async Teams channel: send Adaptive Cards over ``httpx.AsyncClient``.

The async counterpart of :mod:`.teams`; both share card construction from
:mod:`.teams_cards`. It self-registers as the ``teams_async`` channel, so async
callers resolve it with ``ctx.notifications.get(AsyncTeamsNotifier)`` and never
block the event loop.
"""

import logging
from typing import override

import httpx
from microsoft_teams.cards import AdaptiveCard
from mpt_extension_contrib.custom_notifications.base import Notification, NotificationChannel
from mpt_extension_contrib.custom_notifications.channels.teams import resolve_config
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


class AsyncTeamsNotifier(Notification):
    """Base class a custom async Teams implementation subclasses.

    Concrete channels override every method; the registry resolves a channel by
    the notifier base class it inherits (see :meth:`NotificationRegistry.get`).
    """

    async def send_warning(
        self,
        title: str,
        text: str,
        *,
        button: Button | None = None,
        facts: FactsSection | None = None,
    ) -> None:
        """Send a warning-severity notification without blocking the event loop."""
        raise NotImplementedError

    async def send_success(
        self,
        title: str,
        text: str,
        *,
        button: Button | None = None,
        facts: FactsSection | None = None,
    ) -> None:
        """Send a success-severity notification without blocking the event loop."""
        raise NotImplementedError

    async def send_error(
        self,
        title: str,
        text: str,
        *,
        button: Button | None = None,
        facts: FactsSection | None = None,
    ) -> None:
        """Send an error-severity notification without blocking the event loop."""
        raise NotImplementedError

    async def send_exception(
        self,
        title: str,
        text: str,
        *,
        button: Button | None = None,
        facts: FactsSection | None = None,
    ) -> None:
        """Send an exception-severity notification without blocking the event loop."""
        raise NotImplementedError

    async def send_card(self, card: AdaptiveCard) -> None:
        """Send an already-built Adaptive Card without blocking the event loop."""
        raise NotImplementedError


class AsyncTeamsNotifications(AsyncTeamsNotifier):
    """Send Adaptive Cards to a Teams channel via ``httpx.AsyncClient``."""

    def __init__(self, *, webhook_url: str, enabled: bool) -> None:
        self._webhook_url = webhook_url
        self._enabled = enabled

    @override
    async def send_warning(
        self,
        title: str,
        text: str,
        *,
        button: Button | None = None,
        facts: FactsSection | None = None,
    ) -> None:
        """Post a warning-styled Adaptive Card without blocking the event loop."""
        card = severity_card(title, text, "warning", button=button, facts=facts)
        await self.send_card(card)

    @override
    async def send_success(
        self,
        title: str,
        text: str,
        *,
        button: Button | None = None,
        facts: FactsSection | None = None,
    ) -> None:
        """Post a success-styled Adaptive Card without blocking the event loop."""
        card = severity_card(title, text, "success", button=button, facts=facts)
        await self.send_card(card)

    @override
    async def send_error(
        self,
        title: str,
        text: str,
        *,
        button: Button | None = None,
        facts: FactsSection | None = None,
    ) -> None:
        """Post an error-styled Adaptive Card without blocking the event loop."""
        card = severity_card(title, text, "error", button=button, facts=facts)
        await self.send_card(card)

    @override
    async def send_exception(
        self,
        title: str,
        text: str,
        *,
        button: Button | None = None,
        facts: FactsSection | None = None,
    ) -> None:
        """Post an exception-styled Adaptive Card without blocking the event loop."""
        card = severity_card(title, text, "exception", button=button, facts=facts)
        await self.send_card(card)

    @override
    async def send_card(self, card: AdaptiveCard) -> None:
        """Post an already-built Adaptive Card; webhook errors are logged, not raised.

        A no-op when the channel is disabled.
        """
        if not self._enabled:
            logger.info(_DISABLED_LOG)
            return
        try:
            async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
                response = await client.post(self._webhook_url, json=payload(card))
                response.raise_for_status()
        except httpx.HTTPError:
            logger.exception(_FAILED_LOG)


def _build(settings: TeamsSettings) -> AsyncTeamsNotifications | None:
    """Build the async Teams channel from settings, or ``None`` when disabled."""
    webhook_url = resolve_config(settings)
    if webhook_url is None:
        return None
    return AsyncTeamsNotifications(webhook_url=webhook_url, enabled=True)


channel: NotificationChannel[TeamsSettings] = NotificationChannel(
    name="teams_async",
    build=_build,
)
