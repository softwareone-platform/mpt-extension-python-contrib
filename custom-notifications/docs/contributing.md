# Contributing

Keep the core (`base`, `registry`, `discovery`, `context`) free of channel
dependencies. Only channel modules under `channels/` may import a channel SDK.
Update [architecture.md](architecture.md) when the public API or a channel
contract changes.

## Adding a channel

1. Add the channel's runtime dependencies as an extra in
   [`../pyproject.toml`](../pyproject.toml), and mirror them in the `dev`
   dependency group so the channel is covered by tests.
2. Implement the channel under `channels/<name>.py`: a settings `Protocol`, a
   `<Name>Notifier` `Protocol` for custom implementations, the concrete sender,
   a `build(settings)` factory returning `None` when unconfigured, and a
   module-level `channel = NotificationChannel(name=..., build=...)`.
3. Advertise the channel with a `mpt_extension_contrib.custom_notifications.channels`
   entry point in `pyproject.toml`.
4. Import the channel SDK at module level; do not add lazy in-function imports
   (discovery already loads channels lazily and skips them on `ImportError`).

Keep channels free of product-specific business logic: templates, recipients,
and context builders belong in the consumer.

Use package-scoped validation with `pkg=custom-notifications`. Follow the
repository-wide [contributing workflow](../../docs/contributing.md) for
dependency changes, validation commands, and pre-commit expectations.
