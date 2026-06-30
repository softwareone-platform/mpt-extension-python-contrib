"""Named lookup of configured notification channels."""

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
        """Return the registered channel that satisfies ``notifier_type``.

        Args:
            notifier_type: The channel protocol (must be ``runtime_checkable``) or
                class that identifies the channel.

        Returns:
            The single registered channel that satisfies ``notifier_type``.

        Raises:
            KeyError: When no registered channel satisfies ``notifier_type``.
            LookupError: When more than one registered channel satisfies it.
        """
        matches = [
            channel for channel in self._channels.values() if isinstance(channel, notifier_type)
        ]
        if not matches:
            raise KeyError(f"no channel satisfies {notifier_type.__name__}")
        if len(matches) > 1:
            raise LookupError(f"multiple channels satisfy {notifier_type.__name__}")
        return matches[0]

    def __contains__(self, name: str) -> bool:
        return name in self._channels
