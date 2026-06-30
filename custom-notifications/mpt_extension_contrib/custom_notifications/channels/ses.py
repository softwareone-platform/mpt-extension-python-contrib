"""AWS SES channel: send HTML emails through boto3 SES.

This module imports ``boto3`` at module level, so it is importable only when the
``ses`` extra is installed. Channel discovery loads it lazily and skips it on
``ImportError``, which keeps the extra optional for consumers that do not use SES.
"""

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import boto3
import jinja2
from botocore.exceptions import BotoCoreError, ClientError
from mpt_extension_contrib.custom_notifications.base import NotificationChannel

logger = logging.getLogger(__name__)

_CHARSET = "UTF-8"
# Autoescape so substituted values are HTML-escaped while literal template
# markup (and CSS braces) stay intact; StrictUndefined surfaces missing keys.
_JINJA = jinja2.Environment(autoescape=True, undefined=jinja2.StrictUndefined)


class SesSettings(Protocol):
    """Settings the SES channel reads."""

    aws_ses_region: str | None
    aws_ses_sender: str | None
    aws_ses_access_key: str | None
    aws_ses_secret_key: str | None
    email_notifications_enabled: bool


@dataclass(frozen=True)
class EmailNotificationTemplate:
    """An email subject and HTML body rendered with Jinja2.

    ``subject`` and ``body`` are Jinja2 source: ``{{ variable }}`` placeholders,
    ``{% if %}``/``{% for %}`` blocks and filters are supported. Values substituted
    into the HTML ``body`` are autoescaped, so CSS braces stay literal and a
    multi-line styled HTML email can live in its own file; the ``subject`` is
    rendered as plain text and is not escaped. Consumers keep their own templates;
    the channel ships no product-specific ones.
    """

    subject: str
    body: str

    @classmethod
    def from_file(cls, subject: str, body_path: str | Path) -> "EmailNotificationTemplate":
        """Build a template whose ``body`` is the HTML file read from ``body_path``."""
        return cls(subject=subject, body=Path(body_path).read_text(encoding="utf-8"))

    def render(self, context: Mapping[str, object]) -> "EmailNotificationTemplate":
        """Return a copy with ``subject`` and ``body`` rendered from ``context``."""
        # The body is HTML (autoescaped), but a subject is delivered as plain
        # text, so wrap it to opt out of the environment's HTML autoescaping.
        plain_subject = f"{{% autoescape false %}}{self.subject}{{% endautoescape %}}"
        return EmailNotificationTemplate(
            subject=_JINJA.from_string(plain_subject).render(**context),
            body=_JINJA.from_string(self.body).render(**context),
        )


@runtime_checkable
class SesNotifier(Protocol):
    """Contract a custom SES implementation must preserve."""

    def send_email(self, recipients: list[str], subject: str, body: str) -> bool:
        """Send an HTML email; return whether it was sent."""

    def send_template(
        self,
        recipients: list[str],
        template: EmailNotificationTemplate,
        context: Mapping[str, object],
    ) -> bool:
        """Render ``template`` with ``context`` and send it; return whether it was sent."""


class SesNotifications:
    """Send HTML emails to recipients through AWS SES."""

    def __init__(
        self,
        *,
        sender: str,
        enabled: bool,
        region: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
    ) -> None:
        client_kwargs: dict[str, str] = {}
        if region:
            client_kwargs["region_name"] = region
        if access_key and secret_key:
            client_kwargs["aws_access_key_id"] = access_key
            client_kwargs["aws_secret_access_key"] = secret_key
        self._client_kwargs = client_kwargs
        self._sender = sender
        self._enabled = enabled

    def send_email(self, recipients: list[str], subject: str, body: str) -> bool:
        """Send an HTML email to ``recipients``; errors are logged, not raised.

        Returns ``True`` when SES accepted the message, ``False`` when the
        channel is disabled or SES rejected it.
        """
        if not self._enabled:
            logger.info("SES email notifications are disabled; skipping send")
            return False
        message = {
            "Subject": {"Data": subject, "Charset": _CHARSET},
            "Body": {"Html": {"Data": body, "Charset": _CHARSET}},
        }
        try:
            self._client.send_email(
                Source=self._sender,
                Destination={"ToAddresses": recipients},
                Message=message,
            )
        except (ClientError, BotoCoreError):
            logger.exception("Failed to send SES email notification")
            return False
        return True

    def send_template(
        self,
        recipients: list[str],
        template: EmailNotificationTemplate,
        context: Mapping[str, object],
    ) -> bool:
        """Render ``template`` with ``context`` and send it via :meth:`send_email`."""
        rendered = template.render(context)
        return self.send_email(recipients, rendered.subject, rendered.body)

    @cached_property
    def _client(self) -> Any:
        # Created lazily on first send: a missing region/credentials cannot then
        # fail build_registry(), and a disabled channel never builds a client.
        # Without explicit credentials boto3 uses its default chain
        # (IAM role / IRSA / shared config).
        return boto3.client("ses", **self._client_kwargs)


def _build(settings: SesSettings) -> SesNotifications | None:
    """Build the SES channel from settings, or ``None`` when no sender is set.

    Region and credentials are optional: when unset, boto3 falls back to its
    default region/credential chain (IAM role, IRSA, shared config).
    """
    # Read defensively: settings that do not declare the SES fields (e.g. an
    # extension using only another channel) simply yield no SES channel rather
    # than raising AttributeError when every channel is built from one object.
    sender = getattr(settings, "aws_ses_sender", None)
    if not sender:
        return None
    return SesNotifications(
        sender=sender,
        enabled=settings.email_notifications_enabled,
        region=settings.aws_ses_region,
        access_key=settings.aws_ses_access_key,
        secret_key=settings.aws_ses_secret_key,
    )


channel: NotificationChannel[SesSettings] = NotificationChannel(name="aws_ses", build=_build)
"""Entry-point descriptor discovered by :func:`build_registry`."""
