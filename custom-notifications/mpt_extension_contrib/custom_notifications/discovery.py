"""Discover installed channels and assemble a registry from settings."""

import logging
from collections.abc import Iterator
from importlib.metadata import entry_points
from typing import Any

from mpt_extension_contrib.custom_notifications.base import (
    MissingDependencyError,
    NotificationChannel,
    NotificationSettings,
)
from mpt_extension_contrib.custom_notifications.registry import NotificationRegistry

ENTRY_POINT_GROUP = "mpt_extension_contrib.custom_notifications.channels"

logger = logging.getLogger(__name__)


def _iter_channels() -> Iterator[NotificationChannel[Any]]:
    """Yield every channel whose distribution and optional extra are installed.

    A channel whose module cannot be imported (its extra is not installed) is
    skipped rather than failing discovery.
    """
    for entry_point in entry_points(group=ENTRY_POINT_GROUP):
        try:
            yield entry_point.load()
        except ImportError as exc:
            logger.debug("notification channel %r is unavailable: %s", entry_point.name, exc)


def build_registry(settings: NotificationSettings) -> NotificationRegistry:
    """Build a registry of the channels that are installed and configured.

    A channel whose optional extra is not installed is skipped, and so is a
    channel whose factory returns ``None`` because it is not configured in
    ``settings``.

    Args:
        settings: Settings object the channel factories read from. It must
            structurally satisfy the settings protocol of every configured
            channel.

    Returns:
        A registry holding one entry per installed, configured channel.
    """
    registry = NotificationRegistry()
    for channel in _iter_channels():
        if channel.name in registry:
            continue
        try:
            notifier = channel.build(settings)
        except MissingDependencyError as exc:
            logger.debug("notification channel %r is unavailable: %s", channel.name, exc)
            continue
        if notifier is not None:
            registry.register(channel.name, notifier)
    return registry
