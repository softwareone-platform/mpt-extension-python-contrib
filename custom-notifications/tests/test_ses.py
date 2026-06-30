import pytest
from botocore.exceptions import BotoCoreError, ClientError
from mpt_extension_contrib.custom_notifications import build_registry
from mpt_extension_contrib.custom_notifications.channels.ses import (
    EmailNotificationTemplate,
    SesNotifications,
    SesNotifier,
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
    return SesNotifications(
        sender="noreply@example.com",
        enabled=True,
        region="us-east-1",
        access_key="AKIAEXAMPLE",
        secret_key="secret",
    )


def test_build_includes_configured_ses(ses_client, ses_settings):
    registry = build_registry(ses_settings)

    result = registry.get(SesNotifier)

    assert result is not None


def test_build_skips_unconfigured_ses(empty_settings):
    registry = build_registry(empty_settings)

    with pytest.raises(KeyError):
        registry.get(SesNotifier)


def test_client_is_created_lazily(ses_factory):
    SesNotifications(sender="noreply@example.com", enabled=True)  # act

    ses_factory.assert_not_called()


def test_passes_static_credentials_when_set(ses_factory, notifier):
    notifier.send_email(_RECIPIENTS, "Subject", "<p>Body</p>")  # act

    kwargs = ses_factory.call_args.kwargs
    assert kwargs["aws_access_key_id"] == "AKIAEXAMPLE"
    assert kwargs["aws_secret_access_key"] == "secret"
    assert kwargs["region_name"] == "us-east-1"


def test_omits_credentials_for_default_chain(ses_factory):
    notifier = SesNotifications(sender="noreply@example.com", enabled=True)

    notifier.send_email(_RECIPIENTS, "Subject", "Body")  # act

    kwargs = ses_factory.call_args.kwargs
    assert "aws_access_key_id" not in kwargs
    assert "region_name" not in kwargs


def test_send_email_returns_true_on_success(notifier):
    result = notifier.send_email(_RECIPIENTS, "Subject", "<p>Body</p>")

    assert result is True


def test_send_email_posts_expected_payload(ses_client, notifier):
    notifier.send_email(_RECIPIENTS, "Subject", "<p>Body</p>")  # act

    kwargs = ses_client.send_email.call_args.kwargs
    assert kwargs["Source"] == "noreply@example.com"
    assert kwargs["Destination"] == {"ToAddresses": _RECIPIENTS}


def test_send_email_disabled_returns_false(ses_factory):
    disabled = SesNotifications(sender="noreply@example.com", enabled=False)

    result = disabled.send_email(_RECIPIENTS, "Subject", "Body")

    assert result is False
    ses_factory.assert_not_called()  # disabled never even builds a client


def test_template_render_formats_subject_and_body():
    template = EmailNotificationTemplate(
        subject="Order {{ order }}",
        body="<p>{{ order }} ready</p>",
    )

    result = template.render({"order": "ORD-1"})

    assert result == EmailNotificationTemplate(subject="Order ORD-1", body="<p>ORD-1 ready</p>")


def test_render_does_not_escape_subject():
    template = EmailNotificationTemplate(subject="Order {{ order }}", body="<p>x</p>")

    result = template.render({"order": "A & B <Ltd>"})

    assert result.subject == "Order A & B <Ltd>"


def test_render_escapes_values_keeps_css():
    template = EmailNotificationTemplate(
        subject="Order",
        body="<style>body { margin: 0; }</style><p>{{ customer }}</p>",
    )

    result = template.render({"customer": "A & B <Ltd>"})

    assert result.body == "<style>body { margin: 0; }</style><p>A &amp; B &lt;Ltd&gt;</p>"


def test_from_file_reads_body(tmp_path):
    body_file = tmp_path / "deploy.html"
    body_file.write_text("<p>Order {{ order }}</p>", encoding="utf-8")

    result = EmailNotificationTemplate.from_file(subject="Deploy", body_path=body_file)

    assert result == EmailNotificationTemplate(subject="Deploy", body="<p>Order {{ order }}</p>")


def test_send_template_renders_and_sends(ses_client, notifier):
    template = EmailNotificationTemplate(subject="Order {{ order }}", body="<p>{{ order }}</p>")

    result = notifier.send_template(_RECIPIENTS, template, {"order": "ORD-1"})

    kwargs = ses_client.send_email.call_args.kwargs
    assert result is True
    assert kwargs["Message"]["Subject"]["Data"] == "Order ORD-1"


@pytest.mark.parametrize(
    "error",
    [
        ClientError({"Error": {"Code": "MessageRejected", "Message": "no"}}, "SendEmail"),
        BotoCoreError(),
    ],
)
def test_send_email_swallows_boto_errors(ses_client, notifier, error):
    ses_client.send_email.side_effect = error

    result = notifier.send_email(_RECIPIENTS, "Subject", "Body")

    assert result is False
