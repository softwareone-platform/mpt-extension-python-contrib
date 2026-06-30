import pytest
from mpt_extension_contrib.custom_notifications import NotificationRegistry


class _Email:
    kind = "email"


class _Chat:
    kind = "chat"


@pytest.fixture
def registry():
    return NotificationRegistry()


def test_register_and_get(registry):
    notifier = _Email()
    registry.register("a", notifier)

    result = registry.get(_Email)

    assert result is notifier


def test_register_duplicate_raises(registry):
    registry.register("a", _Email())

    with pytest.raises(ValueError, match="already registered"):
        registry.register("a", _Email())


def test_register_override(registry):
    registry.register("a", _Email())
    replacement = _Email()
    registry.register("a", replacement, override=True)

    result = registry.get(_Email)

    assert result is replacement


def test_get_unregistered_type_raises_key_error(registry):
    registry.register("a", _Email())

    with pytest.raises(KeyError):
        registry.get(_Chat)


def test_get_ambiguous_raises_lookup_error(registry):
    registry.register("a", _Email())
    registry.register("b", _Email())

    with pytest.raises(LookupError, match="multiple channels"):
        registry.get(_Email)


def test_contains(registry):
    registry.register("a", _Email())

    result = "a" in registry

    assert result is True
