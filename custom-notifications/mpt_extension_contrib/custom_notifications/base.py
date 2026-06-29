"""Core contracts shared by every notification channel."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@runtime_checkable
class Notification(Protocol):
    """Marker contract implemented by every notification channel.

    Channels expose their own methods through a channel-specific protocol
    (for example ``TeamsNotifier``); this marker only gives the registry a
    common bound.
    """


class NotificationSettings(Protocol):
    """Marker for the settings object a channel factory reads from.

    Each channel narrows this with its own protocol describing the fields it
    needs (for example ``TeamsSettings``). The settings object passed to
    :func:`build_registry` must structurally satisfy the protocols of every
    configured channel.
    """


class MissingDependencyError(ImportError):
    """Raised when a channel's optional extra is not installed."""


@dataclass(frozen=True)
class NotificationChannel[SettingsT: NotificationSettings]:
    """A self-describing channel discovered through entry points.

    Attributes:
        name: Registry key the channel is exposed under.
        build: Factory returning a configured notifier, or ``None`` when the
            channel is not configured in the given settings. It may raise
            :class:`MissingDependencyError` when its optional extra is absent.
    """

    name: str
    build: Callable[[SettingsT], Notification | None]
