# Testing

Tests for `mpt-extension-contrib-fixtures` live under [`../tests/`](../tests), one
file per module (`test_factories.py`, `test_parameters.py`, `test_scenarios.py`,
`test_errors.py`, `test_plugin.py`).

The plugin is tested the canonical way — `test_plugin.py` uses the `pytester`
fixture to run an inline pytest session that consumes the registered fixtures.
The `plugin.py` entry-point module is loaded during pytest startup, before
coverage instrumentation, so it is excluded from coverage (see
[docs/architecture.md](architecture.md) for the full rationale).

Use package-scoped test commands with `pkg=fixtures`. See the
repository-wide [testing strategy](../../docs/testing.md).
