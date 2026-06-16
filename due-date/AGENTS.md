# AGENTS.md

This module is the example public due-date helper package.

Read in this order:

1. [README.md](README.md) for the module purpose.
2. [docs/architecture.md](docs/architecture.md) for the public API boundary.
3. [docs/contributing.md](docs/contributing.md) before changing this module.
4. [docs/testing.md](docs/testing.md) before changing tests.
5. [docs/releases.md](docs/releases.md) before releasing this module.
6. [../AGENTS.md](../AGENTS.md) for repository-wide rules and validation commands.

Operational guidance:

- Keep the public API under `mpt_extension_contrib.due_date`.
- Add tests under [`tests/`](tests) for every behavior change.
- Run `make check-all pkg=due-date` from the repository root while iterating.
