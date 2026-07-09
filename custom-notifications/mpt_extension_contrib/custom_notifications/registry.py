"""Named lookup of configured notification channels."""

from typing import cast

from mpt_extension_contrib.custom_notifications.base import Notification


class NotificationRegistry:
    """Named lookup of configured notification channels."""

    def __init__(self) -> None:
        self._channels: dict[str, Notification] = {}

    def register(self, name: str, notifier: Notification, *, override: bool = False) -> None:
        """Register ``notifier`` under ``name``.

        Args:
            name: Registry key.
            notifier: Configured channel instance.
            override: Allow replacing an already-registered channel.

        Raises:
            ValueError: When ``name`` is already taken and ``override`` is false.
        """
        if name in self._channels and not override:
            raise ValueError(f"notification channel '{name}' is already registered")
        self._channels[name] = notifier

    def get[NotifierT: Notification](self, notifier_type: type[NotifierT]) -> NotifierT:
        """Return the registered channel that implements ``notifier_type``.

        Matching is nominal: a channel implements ``notifier_type`` when its class
        inherits that protocol. This distinguishes a sync channel from its async
        sibling even when they share method names, which a structural
        ``isinstance`` check (that ignores ``async``) cannot.

        Args:
            notifier_type: The channel protocol the notifier class implements.

        Returns:
            The single registered channel that implements ``notifier_type``.

        Raises:
            KeyError: When no registered channel implements ``notifier_type``.
            LookupError: When more than one registered channel implements it.
        """
        matches = [
            channel for channel in self._channels.values() if notifier_type in type(channel).mro()
        ]
        if not matches:
            raise KeyError(f"no channel implements {notifier_type.__name__}")
        if len(matches) > 1:
            raise LookupError(f"multiple channels implement {notifier_type.__name__}")
        # The nominal ``mro()`` check above guarantees the match is a ``NotifierT``;
        # unlike ``isinstance`` it does not narrow the type, so cast explicitly.
        return cast("NotifierT", matches[0])

    def __contains__(self, name: str) -> bool:
        return name in self._channels
