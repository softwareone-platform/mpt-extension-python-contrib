# Usage

This guide covers installing and configuring the library, sending notifications
from pipelines and jobs, and writing your own channel.

## 1. Install the channels you need

Each channel is an optional-dependency extra. A base install pulls no channel
dependencies; request the channels you use:

```bash
pip install "mpt-extension-contrib-custom-notifications[teams,ses]"
```

## 2. Configure channels through settings

A channel is configured by the fields its settings `Protocol` declares. The Teams
channel reads `teams_webhook_url` and `teams_notifications_enabled`; SES reads
`aws_ses_*` and `email_notifications_enabled`. Inherit each installed channel's
settings protocol on the extension settings so the contract is type-checked:

```python
from dataclasses import dataclass

from mpt_extension_sdk.settings.extension import BaseExtensionSettings

from mpt_extension_contrib.custom_notifications.channels.ses import SesSettings
from mpt_extension_contrib.custom_notifications.channels.teams import TeamsSettings


@dataclass(frozen=True)
class ExtensionSettings(BaseExtensionSettings, TeamsSettings, SesSettings):
    teams_webhook_url: str | None = None  # from EXTENSION_CONFIG["MSTEAMS_WEBHOOK_URL"]
    teams_notifications_enabled: bool = False
    aws_ses_region: str | None = None
    aws_ses_sender: str | None = None
    aws_ses_access_key: str | None = None
    aws_ses_secret_key: str | None = None
    email_notifications_enabled: bool = False
```

A channel is registered only when its settings field is set. Leaving
`teams_webhook_url` unset means the `teams` channel is simply absent — no error,
no configuration required for channels you do not use. Setting
`teams_notifications_enabled = False` keeps the channel registered but makes
sending a no-op, so you can turn Teams off without removing the webhook.

### Get the Teams webhook URL

Office 365 connectors are retired, so the webhook URL comes from the Teams
**Workflows** app (Power Automate), not a connector:

1. In Teams, open the target **team → channel**.
2. Select **More options (...)** next to the channel → **Workflows**.
3. Choose the template **Post to a channel when a webhook request is received**.
4. Sign in, set the **Team** and **Channel**, then **Save**.
5. Copy the generated URL (`https://prod-…logic.azure.com/…`) — this is the
   value for `teams_webhook_url` (it is always HTTPS).

The channel POSTs an Adaptive Card envelope
(`{"type": "message", "attachments": [{"contentType": ".card.adaptive", …}]}`),
so the workflow must forward that payload to its *Post card* action; the default
incoming-webhook template does. See the Microsoft Learn guide,
[Create incoming webhooks with Workflows](https://learn.microsoft.com/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook#create-webhooks-using-workflows).

## 3. Build the registry

`build_registry(settings)` discovers every installed channel and registers the
configured ones. It is the single entry point; everything else is sugar over it.

### In a pipeline (via the context mixin)

Mix `NotificationsContextMixin` into the extension context. It reads the standard
`ext_settings`, so there is nothing else to wire; the registry is built once,
lazily, on first access:

```python
from mpt_extension_contrib.custom_notifications import NotificationsContextMixin


class OrderContext(NotificationsContextMixin, SdkOrderContext): ...


# in a step:
ctx.notifications.get(TeamsNotifier).send_error("Sync failed", str(exc))
```

### In a job, command, or service (no context)

Jobs have no `OrderContext`, so call `build_registry(settings)` directly:

```python
from mpt_extension_contrib.custom_notifications import build_registry
from mpt_extension_contrib.custom_notifications.channels.teams import TeamsNotifier

registry = build_registry(extension_settings)
registry.get(TeamsNotifier).send_warning("PLS mismatch", details)
```

Or construct a single channel directly when you do not need the registry:

```python
from mpt_extension_contrib.custom_notifications.channels.teams import TeamsNotifications

teams = TeamsNotifications(webhook_url=settings.EXTENSION_CONFIG["MSTEAMS_WEBHOOK_URL"])
teams.send_exception("Billing job failed", str(exc))
```

## 4. Send notifications

`get(NotifierProtocol)` returns the registered channel that satisfies the
protocol, typed as that protocol and checked at runtime. The Teams channel
exposes four severity helpers plus a raw-card escape hatch:

```python
from mpt_extension_contrib.custom_notifications.channels.teams import (
    Button,
    FactsSection,
    TeamsNotifier,
)

teams = registry.get(TeamsNotifier)
teams.send_error(
    "Agreement sync failed",
    str(exc),
    button=Button(label="Open agreement", url=agreement_url),
    facts=FactsSection(title="Context", entries={"Agreement": agreement_id}),
)
```

The SES channel sends HTML email and returns whether SES accepted the message:

```python
from mpt_extension_contrib.custom_notifications.channels.ses import SesNotifier

sent = registry.get(SesNotifier).send_email(
    ["services@example.com"],
    "New AWS account pending deployment",
    "<p>Order ORD-1 needs manual deployment.</p>",
)
```

When you keep a set of templates, `EmailNotificationTemplate` holds a subject and
HTML body written as **Jinja2** (`{{ variable }}` placeholders, `{% if %}` /
`{% for %}` blocks, filters). `send_template` renders it with a context and sends.
Substituted values are HTML-escaped, so a value can't break the markup and CSS
braces in the body stay literal:

```python
from mpt_extension_contrib.custom_notifications.channels.ses import (
    EmailNotificationTemplate,
    SesNotifier,
)

DEPLOY_PENDING = EmailNotificationTemplate(
    subject="New AWS account pending deployment",
    body="<p>Order {{ order_id }} needs manual deployment.</p>",
)

registry.get(SesNotifier).send_template(
    ["services@example.com"],
    DEPLOY_PENDING,
    {"order_id": "ORD-1"},
)
```

Multi-line HTML emails are easier to keep in their own file than inline in
Python. `EmailNotificationTemplate.from_file(subject, body_path)` reads the body
from an `.html` file shipped with your package:

```python
from pathlib import Path

TEMPLATES = Path(__file__).parent / "templates"

DEPLOY_PENDING = EmailNotificationTemplate.from_file(
    subject="New AWS account pending deployment",
    body_path=TEMPLATES / "deploy_pending.html",
)
```

```html
<!-- deploy_pending.html -->
<html><head><style>body { margin: 0; font-size: 16px; }</style></head>
<body>
  <p>Order {{ order_id }} needs manual deployment.</p>
  {% if error %}<p>Error: {{ error }}</p>{% endif %}
</body></html>
```

Recipients and the templates themselves are the consumer's responsibility — the
channel ships no product templates. To bypass templating entirely, build the
subject/body yourself and call `send_email` directly.

Channel send methods never raise on transport errors: a failed webhook is logged,
not propagated, so a notification never breaks the business flow.

## 5. Write your own channel

A channel is any object that satisfies the `Notification` marker protocol, plus a
`NotificationChannel` descriptor that builds it from settings. There are two ways
to add one.

### Option A — runtime registration (in-process, no packaging)

Register an instance under any key. This also replaces a built-in channel when
`override=True`:

```python
registry.register("teams", MyTeamsNotifications(...), override=True)
```

Use this for a one-off or extension-local implementation. The instance only has
to provide the methods callers expect (for `teams`, the `TeamsNotifier`
protocol).

### Option B — a discoverable channel (own distribution)

Ship the channel as its own package so it self-registers wherever it is
installed. Steps:

1. **Settings protocol** — declare the fields the channel reads:

   ```python
   from typing import Protocol


   class SlackSettings(Protocol):
       slack_webhook_url: str | None
   ```

2. **Notifier protocol** (`runtime_checkable`) — the lookup key for
   `registry.get(...)` and the contract custom implementations preserve:

   ```python
   from typing import Protocol, runtime_checkable


   @runtime_checkable
   class SlackNotifier(Protocol):
       def send_error(self, title: str, text: str) -> None: ...
   ```

3. **Sender** — the concrete implementation. Import the channel SDK at module
   level; discovery skips the channel on `ImportError` when the extra is absent:

   ```python
   import httpx


   class SlackNotifications:
       def __init__(self, *, webhook_url: str) -> None:
           self._webhook_url = webhook_url

       def send_error(
           self, title: str, text: str
       ) -> None: ...  # POST to self._webhook_url; log and swallow transport errors
   ```

4. **Factory + descriptor** — return `None` when unconfigured, and expose a
   module-level `channel`:

   ```python
   from mpt_extension_contrib.custom_notifications import NotificationChannel


   def _build(settings: SlackSettings) -> SlackNotifications | None:
       if not settings.slack_webhook_url:
           return None
       return SlackNotifications(webhook_url=settings.slack_webhook_url)


   channel: NotificationChannel[SlackSettings] = NotificationChannel(name="slack", build=_build)
   ```

5. **Entry point + extra** — advertise the channel and gate its dependencies in
   the channel package's `pyproject.toml`:

   ```toml
   [project.optional-dependencies]
   slack = ["httpx>=0.28,<1"]

   [project.entry-points."mpt_extension_contrib.custom_notifications.channels"]
   slack = "my_package.slack:channel"
   ```

### Checklist for a discoverable channel

- The channel's optional dependencies are an **extra**, not base dependencies.
- The channel module **imports its SDK at module level** (no in-function imports);
  discovery loads it lazily and skips it on `ImportError`.
- `build` reads only from the settings protocol and returns `None` when the
  channel is not configured — never raises for missing configuration.
- The sender carries **no product-specific logic** (recipients, templates, and
  context building stay in the consumer).
- An entry point under `mpt_extension_contrib.custom_notifications.channels`
  exposes a module-level `NotificationChannel`.
- The channel **name is unique**; on a duplicate name the first discovered
  channel wins and later ones are skipped.

Once installed, the channel appears in `build_registry(settings)` automatically
when its extra is installed and its settings are configured.
