# mpt-extension-contrib-fixtures

Pytest fixtures and [polyfactory](https://polyfactory.litestar.dev/) factories
for MPT-shaped objects (orders, agreements, subscriptions). Factories build
structurally valid SDK models with empty parameters; the product-specific
parameter catalog stays in the consumer.

Installing the package registers a pytest plugin (`pytest11` entry point), so
its fixtures are available without any `conftest.py` wiring.

See [AGENTS.md](AGENTS.md) for the module documentation map.

## Documentation

- [Usage](docs/usage.md)
- [Architecture](docs/architecture.md)
- [Technical Design Review](docs/technical-design-review.md)
- [Contributing](docs/contributing.md)
- [Testing](docs/testing.md)
- [Releases](docs/releases.md)
