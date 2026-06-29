# AGENTS.md

This module is the `reports` contrib package.

Read in this order:

1. [README.md](README.md) for the module purpose.
2. [docs/usage.md](docs/usage.md) for installing, running the pending-orders report, and composing other reports.
3. [docs/architecture.md](docs/architecture.md) for the public API boundary.
4. [docs/contributing.md](docs/contributing.md) before changing this module.
5. [docs/testing.md](docs/testing.md) before changing tests.
6. [docs/releases.md](docs/releases.md) before releasing this module.
7. [../AGENTS.md](../AGENTS.md) for repository-wide rules and validation commands.

Operational guidance:

- Keep the public API under `mpt_extension_contrib.reports` (exported
  from `__init__.py`); keep modules below it internal implementation detail.
- Inject configuration (Confluence credentials, column layout, RQL query)
  through the public API; do not bake in product-specific fields.
- Add tests under [`tests/`](tests) for every behavior change.
- Run `make check-all pkg=reports` from the repository root while iterating.
