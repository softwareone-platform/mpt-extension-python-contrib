# AGENTS.md

This module is the internal shared package for contrib libraries.

Read in this order:

1. [README.md](README.md) for the module purpose.
2. [docs/architecture.md](docs/architecture.md) for module boundaries.
3. [docs/contributing.md](docs/contributing.md) before changing this module.
4. [docs/testing.md](docs/testing.md) before changing tests.
5. [docs/releases.md](docs/releases.md) before releasing this module.
6. [../AGENTS.md](../AGENTS.md) for repository-wide rules and validation commands.

Operational guidance:

- Treat `mpt_extension_contrib.shared` as internal API.
- Keep helpers generic and reusable across contrib modules.
- Add tests under [`tests/`](tests) for every behavior change.
- Run `make check-all pkg=shared` from the repository root while iterating.
