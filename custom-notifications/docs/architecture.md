# Architecture

`mpt-extension-contrib-custom-notifications` provides a pluggable notification registry
and a set of channels, exposed to extensions as `ctx.notifications`.

## Public API boundary

The package root `mpt_extension_contrib.custom_notifications` exports the core:

```python
from mpt_extension_contrib.custom_notifications import (
    NotificationsContextMixin,
    NotificationRegistry,
    build_registry,
    Notification,
    NotificationChannel,
    NotificationSettings,
)
```

- `NotificationsContextMixin` adds a lazily-built `notifications` registry to an
  Extension SDK context, reading the host context's standard `ext_settings`.
- `NotificationRegistry` registers channels by name (`register`) and resolves
  them by type: `get(NotifierProtocol)` returns the single registered channel
  that satisfies the protocol (a `runtime_checkable` check), narrowed to it.
- `build_registry(settings)` discovers installed channels and registers the
  configured ones.
- `Notification` and `NotificationSettings` are marker `Protocol`s. A channel and
  its settings satisfy them structurally — no inheritance required.
- `NotificationChannel(name, build)` is the entry-point descriptor a channel
  advertises.

Channel implementations are **not** exported from the root; they live under
`mpt_extension_contrib.custom_notifications.channels.<name>` and are imported directly
(for example `...channels.teams.TeamsNotifier`).

## Design

- **One distribution, channels behind extras.** Teams and SES are channels of a
  single distribution, each gated by an optional-dependency extra
  (`[teams]`, later `[ses]`). A base install pulls no channel dependencies.
- **Channels self-register via entry points.** Every channel advertises a
  `mpt_extension_contrib.custom_notifications.channels` entry point exposing a
  `NotificationChannel`. `build_registry` iterates the group, so built-in and
  third-party channels are discovered the same way with no consumer wiring.
- **Optional dependencies stay optional.** A channel module imports its channel
  SDK at module level, so the module is importable only when its extra is
  installed. Discovery loads each entry point lazily and skips it on
  `ImportError`. The core never imports a channel SDK.
- **Configuration comes from settings.** Each channel declares its own settings
  `Protocol` (for example `TeamsSettings.teams_webhook_url`) and its factory
  reads from the `ext_settings` object the mixin passes in. The extension
  settings inherit each channel's protocol so the contract is type-checked. No
  product-specific constants are baked in.
- **Channels are transport only.** They carry no product templates, recipients,
  or context builders; those stay in the consumer.

## Behaviour

- `build_registry(settings)` registers a channel only when its factory returns a
  configured instance. A factory returns `None` when its settings are absent, so
  an unconfigured channel is simply not in the registry.
- Duplicate channel names are resolved first-wins; later duplicates are skipped.
- The Teams channel renders an Adaptive Card with `microsoft-teams-cards` and
  POSTs it to a Power Automate Workflows webhook with `httpx`. Severity helpers
  (`send_warning`/`send_success`/`send_error`/`send_exception`) set the card
  colour and emoji; `send_card` posts an already-built card. Webhook errors are
  logged and swallowed so notifications never break the business flow.
