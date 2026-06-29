# AGENTS.md

This module is the `custom-notifications` contrib package.

Read in this order:

1. [README.md](README.md) for the module purpose.
2. [docs/usage.md](docs/usage.md) for installing, configuring, sending, and writing a channel.
3. [docs/architecture.md](docs/architecture.md) for the public API boundary.
4. [docs/contributing.md](docs/contributing.md) before changing this module.
5. [docs/testing.md](docs/testing.md) before changing tests.
6. [docs/releases.md](docs/releases.md) before releasing this module.
7. [../AGENTS.md](../AGENTS.md) for repository-wide rules and validation commands.

Operational guidance:

- Keep the core (`base`, `registry`, `discovery`, `context`) free of channel
  dependencies; only channel modules under `channels/` may import a channel SDK.
- Gate each channel's dependencies behind an extra in
  [`pyproject.toml`](pyproject.toml) and advertise the channel through a
  `mpt_extension_contrib.custom_notifications.channels` entry point.
- A channel module imports its optional dependencies at module level; discovery
  loads it lazily and skips it on `ImportError`, so never import a channel SDK
  from the core.
- Keep channels free of product-specific business logic (templates, recipients,
  and context builders stay in the consumer).
- Add tests under [`tests/`](tests) for every behavior change; dev dependencies
  must include the channel extras so channel code is covered.
- Run `make check-all pkg=custom-notifications` from the repository root while iterating.
