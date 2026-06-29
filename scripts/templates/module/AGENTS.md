# AGENTS.md

This module is the `{{ module }}` contrib package.

Read in this order:

1. [README.md](README.md) for the module purpose.
2. [docs/usage.md](docs/usage.md) for installing and using the module.
3. [docs/architecture.md](docs/architecture.md) for the public API boundary.
4. [docs/contributing.md](docs/contributing.md) before changing this module.
5. [docs/testing.md](docs/testing.md) before changing tests.
6. [docs/releases.md](docs/releases.md) before releasing this module.
7. [../AGENTS.md](../AGENTS.md) for repository-wide rules and validation commands.

Operational guidance:

- Keep the public API under `mpt_extension_contrib.{{ python_name }}`.
- Replace the generated example helper when implementing the real API.
- Add tests under [`tests/`](tests) for every behavior change.
- Run `make check-all pkg={{ module }}` from the repository root while iterating.
