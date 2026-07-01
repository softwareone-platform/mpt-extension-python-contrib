# AGENTS.md

This module is the `fixtures` contrib package.

Read in this order:

1. [README.md](README.md) for the module purpose.
2. [docs/usage.md](docs/usage.md) for installing and using the module.
3. [docs/architecture.md](docs/architecture.md) for the public API boundary.
4. [docs/technical-design-review.md](docs/technical-design-review.md) for the problems, requirements, and how they map to usage.
5. [docs/contributing.md](docs/contributing.md) before changing this module.
6. [docs/testing.md](docs/testing.md) before changing tests.
7. [docs/releases.md](docs/releases.md) before releasing this module.
8. [../AGENTS.md](../AGENTS.md) for repository-wide rules and validation commands.

Operational guidance:

- Public API is re-exported from the package root (`mpt_extension_contrib.fixtures`)
  via a lazy PEP 562 `__getattr__`; implementation lives in the `factories`,
  `parameters`, `scenarios`, and `errors` submodules.
- Factories build structurally valid SDK models with empty parameters only — no
  product-specific parameter values or business logic.
- Resolve implementation lazily in `__init__.py` and `plugin.py` (the `pytest11`
  entry point) so startup registration stays measurable by coverage. See
  [docs/architecture.md](docs/architecture.md) for the coverage rationale and the
  scoped lint ignores it requires.
- Test the plugin with the `pytester` fixture; unit-test each helper directly.
- Add tests under [`tests/`](tests) for every behavior change.
- Run `make check-all pkg=fixtures` from the repository root while iterating.
