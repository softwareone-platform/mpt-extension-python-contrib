"""Context mixin exposing a lazily-built notification registry."""

from functools import cached_property

from mpt_extension_contrib.custom_notifications.base import NotificationSettings
from mpt_extension_contrib.custom_notifications.discovery import build_registry
from mpt_extension_contrib.custom_notifications.registry import NotificationRegistry


class NotificationsContextMixin:
    """Add ``self.notifications`` to an Extension SDK context.

    Mix into a context that exposes ``ext_settings``; the registry is built once
    from those settings on first access. ``ext_settings`` must satisfy the
    settings protocol of every installed channel.
    """

    ext_settings: NotificationSettings

    @cached_property
    def notifications(self) -> NotificationRegistry:
        """Registry of the channels that are installed and configured."""
        return build_registry(self.ext_settings)
