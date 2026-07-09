import pytest
from mpt_extension_contrib.custom_notifications import build_registry
from mpt_extension_contrib.custom_notifications.channels.ses import EmailNotificationTemplate
from mpt_extension_contrib.custom_notifications.channels.ses_async import (
    AsyncSesNotifications,
    AsyncSesNotifier,
)

_BOTO3_CLIENT = "mpt_extension_contrib.custom_notifications.channels.ses.boto3.client"
_RECIPIENTS = ("to@example.com",)


@pytest.fixture
def ses_factory(mocker):
    return mocker.patch(_BOTO3_CLIENT, autospec=True)


@pytest.fixture
def ses_client(ses_factory):
    return ses_factory.return_value


@pytest.fixture
def notifier(ses_client):
    return AsyncSesNotifications(sender="noreply@example.com", enabled=True, region="us-east-1")


def test_build_registers_async_ses(ses_client, ses_settings):
    registry = build_registry(ses_settings)

    result = registry.get(AsyncSesNotifier)

    assert result is not None


async def test_send_email_sends_off_thread(ses_client, notifier):
    result = await notifier.send_email(_RECIPIENTS, "Subject", "<p>Body</p>")

    kwargs = ses_client.send_email.call_args.kwargs
    assert result is True
    assert kwargs["Destination"] == {"ToAddresses": _RECIPIENTS}


async def test_send_template_renders_and_sends(ses_client, notifier):
    template = EmailNotificationTemplate(subject="Order {{ order }}", body="<p>{{ order }}</p>")

    result = await notifier.send_template(_RECIPIENTS, template, {"order": "ORD-1"})

    kwargs = ses_client.send_email.call_args.kwargs
    assert result is True
    assert kwargs["Message"]["Subject"]["Data"] == "Order ORD-1"


async def test_send_email_disabled_returns_false(ses_factory):
    notifier = AsyncSesNotifications(sender="noreply@example.com", enabled=False)

    result = await notifier.send_email(_RECIPIENTS, "Subject", "Body")

    assert result is False
    ses_factory.assert_not_called()
