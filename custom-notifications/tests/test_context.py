from mpt_extension_contrib.custom_notifications import (
    NotificationRegistry,
    NotificationsContextMixin,
)


class _Context(NotificationsContextMixin):
    def __init__(self, settings):
        self.ext_settings = settings


def test_mixin_builds_registry(teams_settings):
    context = _Context(teams_settings)

    result = context.notifications

    assert isinstance(result, NotificationRegistry)


def test_mixin_registers_teams(teams_settings):
    context = _Context(teams_settings)

    result = context.notifications

    assert "teams" in result


def test_mixin_caches_registry(teams_settings):
    context = _Context(teams_settings)

    result = context.notifications

    assert result is context.notifications
