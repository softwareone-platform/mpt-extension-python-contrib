from importlib.metadata import EntryPoint

import pytest
from mpt_extension_contrib.custom_notifications import (
    MissingDependencyError,
    NotificationChannel,
    build_registry,
)
from mpt_extension_contrib.custom_notifications.channels.teams import TeamsNotifier

_ENTRY_POINTS = "mpt_extension_contrib.custom_notifications.discovery.entry_points"


@pytest.fixture
def broken_channel(mocker):
    entry_point = mocker.create_autospec(EntryPoint, instance=True)
    entry_point.name = "broken"
    entry_point.load.side_effect = ImportError("extra not installed")
    mocker.patch(_ENTRY_POINTS, autospec=True).return_value = [entry_point]


@pytest.fixture
def missing_dependency_channel(mocker):
    def factory(_settings):
        raise MissingDependencyError("nope")

    entry_point = mocker.create_autospec(EntryPoint, instance=True)
    entry_point.load.return_value = NotificationChannel(name="x", build=factory)
    mocker.patch(_ENTRY_POINTS, autospec=True).return_value = [entry_point]


@pytest.fixture
def duplicate_channels(mocker):
    first = object()
    channels = [
        NotificationChannel(name="dup", build=lambda _settings: first),
        NotificationChannel(name="dup", build=lambda _settings: object()),
    ]
    entry_points = []
    for channel in channels:
        entry_point = mocker.create_autospec(EntryPoint, instance=True)
        entry_point.load.return_value = channel
        entry_points.append(entry_point)
    mocker.patch(_ENTRY_POINTS, autospec=True).return_value = entry_points
    return first


def test_build_includes_configured_teams(teams_settings):
    registry = build_registry(teams_settings)

    result = registry.get(TeamsNotifier)

    assert result is not None


def test_build_skips_unconfigured_teams(empty_settings):
    registry = build_registry(empty_settings)

    result = "teams" in registry

    assert result is False


def test_build_rejects_non_https_teams(insecure_teams_settings):
    with pytest.raises(ValueError, match="https"):
        build_registry(insecure_teams_settings)


def test_build_skips_unimportable_channel(broken_channel, teams_settings):
    result = "broken" in build_registry(teams_settings)

    assert result is False


def test_build_skips_missing_dependency(missing_dependency_channel, teams_settings):
    result = "x" in build_registry(teams_settings)

    assert result is False


def test_build_dedupes_by_name(duplicate_channels, teams_settings):
    result = build_registry(teams_settings).get(object)

    assert result is duplicate_channels
