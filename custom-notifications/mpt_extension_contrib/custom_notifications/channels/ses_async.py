"""Async AWS SES channel: send HTML emails without blocking the event loop.

The synchronous :class:`.ses.SesNotifications` performs blocking I/O, so this
channel runs it in a worker thread via :func:`asyncio.to_thread` — non-blocking
for the caller with no extra dependency. It self-registers as the
``aws_ses_async`` channel, resolved with ``ctx.notifications.get(AsyncSesNotifier)``.
"""

import asyncio
from collections.abc import Mapping
from typing import override

from mpt_extension_contrib.custom_notifications.base import Notification, NotificationChannel
from mpt_extension_contrib.custom_notifications.channels.ses import (
    EmailNotificationTemplate,
    SesNotifications,
    SesSettings,
    resolve_config,
)


class AsyncSesNotifier(Notification):
    """Base class a custom async SES implementation subclasses.

    Concrete channels override every method; the registry resolves a channel by
    the notifier base class it inherits (see :meth:`NotificationRegistry.get`).
    """

    async def send_email(self, recipients: list[str], subject: str, body: str) -> bool:
        """Send an HTML email without blocking the event loop; return whether it was sent."""
        raise NotImplementedError

    async def send_template(
        self,
        recipients: list[str],
        template: EmailNotificationTemplate,
        context: Mapping[str, object],
    ) -> bool:
        """Render ``template`` and send it without blocking the event loop."""
        raise NotImplementedError


class AsyncSesNotifications(AsyncSesNotifier):
    """Send HTML emails through AWS SES off the event loop via ``asyncio.to_thread``."""

    def __init__(
        self,
        *,
        sender: str,
        enabled: bool,
        region: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
    ) -> None:
        self._sync = SesNotifications(
            sender=sender,
            enabled=enabled,
            region=region,
            access_key=access_key,
            secret_key=secret_key,
        )

    @override
    async def send_email(self, recipients: list[str], subject: str, body: str) -> bool:
        """Run :meth:`.ses.SesNotifications.send_email` off the event loop."""
        return await asyncio.to_thread(self._sync.send_email, recipients, subject, body)

    @override
    async def send_template(
        self,
        recipients: list[str],
        template: EmailNotificationTemplate,
        context: Mapping[str, object],
    ) -> bool:
        """Run :meth:`.ses.SesNotifications.send_template` off the event loop."""
        return await asyncio.to_thread(self._sync.send_template, recipients, template, context)


def _build(settings: SesSettings) -> AsyncSesNotifications | None:
    """Build the async SES channel from settings, or ``None`` when disabled."""
    sender = resolve_config(settings)
    if sender is None:
        return None
    return AsyncSesNotifications(
        sender=sender,
        enabled=True,
        region=settings.aws_ses_region,
        access_key=settings.aws_ses_access_key,
        secret_key=settings.aws_ses_secret_key,
    )


channel: NotificationChannel[SesSettings] = NotificationChannel(
    name="aws_ses_async",
    build=_build,
)
