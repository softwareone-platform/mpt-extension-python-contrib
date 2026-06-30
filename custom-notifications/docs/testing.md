# Testing

Tests for `mpt-extension-contrib-custom-notifications` live under [`../tests/`](../tests):

- `test_registry.py` — `NotificationRegistry`: register and typed `get` (by
  protocol), duplicate-without-override raising, `override`, the unregistered-type
  (`KeyError`) and ambiguous (`LookupError`) cases, and `__contains__`.
- `test_discovery.py` — `build_registry` through its public surface: a configured
  channel is registered and an unconfigured one is not; an unimportable channel
  (extra missing) is skipped; a channel whose factory raises
  `MissingDependencyError` is skipped; duplicate names resolve first-wins.
- `test_context.py` — `NotificationsContextMixin`: builds a registry from
  `ext_settings`, registers configured channels, and caches the result.
- `test_teams.py` — the Teams channel: each severity helper posts the expected
  Adaptive Card (emoji and colour); the Workflows envelope shape; buttons and
  facts render; and webhook/request errors are swallowed.

The Teams tests intercept HTTP with `respx` and assert on the captured request
payload rather than making network calls; discovery tests mock the `entry_points`
boundary with autospec doubles. Channel extras are declared in the `dev`
dependency group so channel code is importable and covered.

Use package-scoped test commands with `pkg=custom-notifications`. Coverage must stay at
the repository threshold. See the repository-wide
[testing strategy](../../docs/testing.md).
