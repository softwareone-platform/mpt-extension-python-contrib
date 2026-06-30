# mpt-extension-contrib-custom-notifications

Shared **notification channels** for SoftwareONE MPT extensions built on the
Extension SDK. Extensions report to a channel (Microsoft Teams today, AWS SES
next) through one registry — `ctx.notifications` — instead of re-implementing a
sender per extension.

Channels are **pluggable**: each is gated by an optional-dependency extra and
self-registers through an entry point, so a base install pulls no channel
dependencies and only the channels you install and configure are exposed.

It consolidates the per-extension notification code previously re-implemented in
the AWS (`swo/notifications/teams.py`) and Adobe (`adobe_vipm/notifications.py`)
extensions.

See [AGENTS.md](AGENTS.md) for the module documentation map.

## Install

```bash
pip install "mpt-extension-contrib-custom-notifications[teams]"
```

The base distribution has no channel dependencies. Each channel is an extra:

| Extra | Pulls in | Channel key |
| --- | --- | --- |
| `teams` | `microsoft-teams-cards`, `httpx` | `teams` |

## Public API

`mpt_extension_contrib.custom_notifications` exposes the core; channel implementations
live under `mpt_extension_contrib.custom_notifications.channels.<name>`.

| Object | Purpose |
| --- | --- |
| `NotificationsContextMixin` | Adds `self.notifications` to an SDK context, built from settings. |
| `NotificationRegistry` | Named lookup of configured channels (`register`, `get`). |
| `build_registry(settings)` | Discover installed channels and register the configured ones. |
| `Notification` | Marker `Protocol` every channel satisfies. |
| `NotificationChannel` | Entry-point descriptor (`name`, `build`) advertised by a channel. |
| `NotificationSettings` | Marker `Protocol` for the settings a channel factory reads. |

Teams channel — `mpt_extension_contrib.custom_notifications.channels.teams` (extra `teams`):

| Object | Purpose |
| --- | --- |
| `TeamsNotifications` | Send Adaptive Cards to a Teams channel via a Workflows webhook. |
| `TeamsNotifier` | `Protocol` a custom Teams implementation must preserve. |
| `TeamsSettings` | `Protocol` describing the settings the channel reads (`teams_webhook_url`, `teams_notifications_enabled`). |
| `Button`, `FactsSection` | Value types for a card link button and a facts section. |

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
it is configured in settings. Asking for a channel that is not registered raises
`KeyError`, so an extension that does not use Teams neither installs the extra
nor configures the webhook.

### Custom channels

A custom implementation only has to satisfy the channel `Protocol`; register it
under any key (use `override=True` to replace a built-in):

```python
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
