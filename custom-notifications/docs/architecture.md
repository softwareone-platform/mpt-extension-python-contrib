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
  whose class **implements** the protocol, narrowed to it. Matching is nominal
  (by inheritance), so a channel and its async sibling are told apart even though
  they share method names — a structural `isinstance` check cannot, because it
  ignores `async`.
- `build_registry(settings)` discovers installed channels and registers the
  configured ones.
- A channel class **inherits** its notifier base class (for example
  `TeamsNotifications(TeamsNotifier)`), so `get` can resolve it nominally and
  mypy verifies conformance. The notifier types are concrete base classes rather
  than `Protocol`s so that `registry.get(TeamsNotifier)` type-checks under
  `mypy --strict` — passing a `Protocol` to a `type[...]` parameter raises
  `type-abstract`. `NotificationSettings` stays a structural marker — settings
  objects satisfy the settings protocols by shape, not inheritance.
- `NotificationChannel(name, build)` is the entry-point descriptor a channel
  advertises.

Channel implementations are **not** exported from the root; they live under
`mpt_extension_contrib.custom_notifications.channels.<name>` and are imported directly
(for example `...channels.teams.TeamsNotifier`).

## Design

- **One distribution, channels behind extras.** Teams and SES are channels of a
  single distribution, each gated by an optional-dependency extra
  (`[teams]`, `[ses]`). A base install pulls no channel dependencies.
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
  configured instance. The enable flag is the master switch: a factory returns
  `None` when its channel is disabled (so a disabled channel is simply not in the
  registry), and **raises `ValueError`** when the channel is enabled but its
  required fields are missing or invalid — an enabled-but-misconfigured channel
  fails loudly instead of being silently skipped. The enable flag is read
  defensively (`getattr`) because every channel is built from one settings
  object, so a settings that does not target a channel is skipped, not an error.
- Duplicate channel names are resolved first-wins; later duplicates are skipped.
- The Teams channel renders an Adaptive Card with `microsoft-teams-cards` and
  POSTs it to a Power Automate Workflows webhook with `httpx`. Severity helpers
  (`send_warning`/`send_success`/`send_error`/`send_exception`) set the card
  colour and emoji; `send_card` posts an already-built card. Webhook errors are
  logged and swallowed so notifications never break the business flow. Its
  factory builds only when `teams_notifications_enabled` is on, and then requires
  a valid HTTPS `teams_webhook_url`.
- The SES channel sends HTML email through boto3 SES; `send_email(...)` returns
  `True` when SES accepted the message and `False` when SES raised
  `ClientError`/`BotoCoreError` (logged, not raised). Its factory builds only
  when `email_notifications_enabled` is on, and then requires `aws_ses_sender`;
  region and credentials stay optional (boto3's default chain), but a partial
  static credential pair is rejected. `EmailNotificationTemplate` renders a
  Jinja2 subject/body (via `send_template`) for consumers that keep templates.
- Async support ships as **sibling channels** that self-register alongside the
  sync ones from the same settings: `teams_async` (`AsyncTeamsNotifications`,
  resolved via `AsyncTeamsNotifier`) and `aws_ses_async` (`AsyncSesNotifications`,
  resolved via `AsyncSesNotifier`). They live in separate modules
  (`channels/teams_async.py`, `channels/ses_async.py`) so async callers never
  block the event loop. Teams uses `httpx.AsyncClient` for real non-blocking I/O;
  SES wraps its blocking `boto3` call in `asyncio.to_thread` (boto3 has no native
  async, and pulling `aioboto3` would break the minimal-dependency rule). The
  async path keeps the same enable-flag guard and error-swallowing as the sync
  one, and Teams card construction is shared through `channels/teams_cards.py`.
