# AGENTS.md

This module is the `due-date` contrib package.

Read in this order:

1. [README.md](README.md) for the module purpose.
2. [docs/usage.md](docs/usage.md) for installing, configuring, and using the steps.
3. [docs/architecture.md](docs/architecture.md) for the public API boundary.
4. [docs/contributing.md](docs/contributing.md) before changing this module.
5. [docs/testing.md](docs/testing.md) before changing tests.
6. [docs/releases.md](docs/releases.md) before releasing this module.
7. [../AGENTS.md](../AGENTS.md) for repository-wide rules and validation commands.

Operational guidance:

- Keep the public API under `mpt_extension_contrib.due_date` limited to the
  pipeline steps, the `DueDateSettings` protocol, and the `DueDateReachedError`
  exception; keep `calculation` and `parameters` internal.
- Keep the steps free of product-specific business logic.
- Add tests under [`tests/`](tests) for every behavior change.
- Run `make check-all pkg=due-date` from the repository root while iterating.
