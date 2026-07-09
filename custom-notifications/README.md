# mpt-extension-contrib-custom-notifications

Shared **notification channels** for SoftwareONE MPT extensions built on the
Extension SDK. Extensions report to a channel (Microsoft Teams or AWS SES email)
through one registry — `ctx.notifications` — instead of re-implementing a sender
per extension.

Channels are **pluggable**: each is gated by an optional-dependency extra and
self-registers through an entry point, so a base install pulls no channel
dependencies and only the channels you install and configure are exposed.

It consolidates the per-extension notification code previously re-implemented in
the AWS (`swo/notifications/teams.py`) and Adobe (`adobe_vipm/notifications.py`)
extensions.

See [AGENTS.md](AGENTS.md) for the module documentation map.

## Install

```bash
pip install "mpt-extension-contrib-custom-notifications[teams,ses]"
```

The base distribution has no channel dependencies. Each channel is an extra:

| Extra | Pulls in | Channel key |
| --- | --- | --- |
| `teams` | `microsoft-teams-cards`, `httpx` | `teams` |
| `ses` | `boto3`, `jinja2` | `aws_ses` |

## Public API

`mpt_extension_contrib.custom_notifications` exposes the core; channel implementations
live under `mpt_extension_contrib.custom_notifications.channels.<name>`.

| Object | Purpose |
| --- | --- |
| `NotificationsContextMixin` | Adds `self.notifications` to an SDK context, built from settings. |
| `NotificationRegistry` | Named lookup of configured channels (`register`, `get`). |
| `build_registry(settings)` | Discover installed channels and register the configured ones. |
| `Notification` | Marker base class every notifier base class extends (`get`'s bound). |
| `NotificationChannel` | Entry-point descriptor (`name`, `build`) advertised by a channel. |
| `NotificationSettings` | Marker `Protocol` for the settings a channel factory reads. |

Teams channel — `mpt_extension_contrib.custom_notifications.channels.teams` (extra `teams`):

| Object | Purpose |
| --- | --- |
| `TeamsNotifications` | Send Adaptive Cards to a Teams channel via a Workflows webhook (`send_*`). |
| `TeamsNotifier` | Base class a custom Teams implementation subclasses (the registry resolves by inheritance). |
| `TeamsSettings` | `Protocol` describing the settings the channel reads (`teams_webhook_url`, `teams_notifications_enabled`). |
| `Button`, `FactsSection` | Value types for a card link button and a facts section. |

Async Teams channel — `mpt_extension_contrib.custom_notifications.channels.teams_async` (channel `teams_async`, extra `teams`):

| Object | Purpose |
| --- | --- |
| `AsyncTeamsNotifications` | Send Adaptive Cards over `httpx.AsyncClient` without blocking the event loop (`send_*`). |
| `AsyncTeamsNotifier` | Base class for the async `send_*` methods; resolve via `ctx.notifications.get(AsyncTeamsNotifier)`. |

SES channel — `mpt_extension_contrib.custom_notifications.channels.ses` (extra `ses`):

| Object | Purpose |
| --- | --- |
| `SesNotifications` | Send HTML emails through AWS SES (`send_email` / `send_template` -> bool). |
| `SesNotifier` | Base class a custom SES implementation subclasses (the registry resolves by inheritance). |
| `SesSettings` | `Protocol` for the settings the channel reads (region, sender, credentials, enable flag). |
| `EmailNotificationTemplate` | Subject + Jinja2 HTML body (`render(context)`; `from_file(subject, body_path)` to load the body from an `.html` file). |

Async SES channel — `mpt_extension_contrib.custom_notifications.channels.ses_async` (channel `aws_ses_async`, extra `ses`):

| Object | Purpose |
| --- | --- |
| `AsyncSesNotifications` | Send HTML emails through AWS SES off the event loop via `asyncio.to_thread` (`send_email` / `send_template` -> bool). |
| `AsyncSesNotifier` | Base class for the async `send_*` methods; resolve via `ctx.notifications.get(AsyncSesNotifier)`. |

## Usage

Make the extension settings satisfy each installed channel's settings protocol
(inherit it so the contract is type-checked), then mix `NotificationsContextMixin`
into the context — it reads the standard `ext_settings`, so no extra wiring:

```python
from dataclasses import dataclass

from mpt_extension_sdk.settings.extension import BaseExtensionSettings

from mpt_extension_contrib.custom_notifications import NotificationsContextMixin
from mpt_extension_contrib.custom_notifications.channels.teams import TeamsSettings


@dataclass(frozen=True)
class ExtensionSettings(BaseExtensionSettings, TeamsSettings):
    # MSTEAMS_WEBHOOK_URL is read from the extension configuration.
    teams_webhook_url: str | None = None


class OrderContext(NotificationsContextMixin, SdkOrderContext): ...
```

Then resolve a channel and send. `get(NotifierProtocol)` returns the registered
channel that satisfies the protocol, typed as that protocol:

```python
from mpt_extension_contrib.custom_notifications.channels.teams import (
    Button,
    FactsSection,
    TeamsNotifier,
)

teams = ctx.notifications.get(TeamsNotifier)
teams.send_error(
    "Agreement sync failed",
    str(exc),
    button=Button(label="Open agreement", url=agreement_url),
    facts=FactsSection(title="Context", entries={"Agreement": agreement_id}),
)
```

A channel appears in the registry only when **both** its extra is installed and
its enable flag (`teams_notifications_enabled` / `email_notifications_enabled`)
is on. `get(...)` on a channel that is not registered raises `KeyError`. Enabling
a channel without its required fields (`teams_webhook_url` / `aws_ses_sender`)
makes `build_registry` raise a clear `ValueError`, so a misconfiguration fails
loudly instead of silently disabling notifications.

### Custom channels

A custom implementation **inherits** the channel `Protocol` (the registry matches
by inheritance); register it under any key (use `override=True` to replace a
built-in):

```python
class MyTeamsNotifications(TeamsNotifier): ...


ctx.notifications.register("teams", MyTeamsNotifications(...), override=True)
```

To make a custom channel discoverable across extensions, ship it as its own
distribution that advertises a `mpt_extension_contrib.custom_notifications.channels`
entry point exposing a `NotificationChannel`.

## Documentation

- [Usage](docs/usage.md) — install, configure, send, and write your own channel
- [Architecture](docs/architecture.md)
- [Contributing](docs/contributing.md)
- [Testing](docs/testing.md)
- [Releases](docs/releases.md)
