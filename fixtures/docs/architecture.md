# Architecture

`mpt-extension-contrib-fixtures` exposes test helpers for MPT-shaped objects.

## Public API

- `mpt_extension_contrib.fixtures` — package root re-exports the public API
  (`OrderFactory`, `AgreementFactory`, `SubscriptionFactory`, `MPTModelFactory`,
  `ParameterBagFactory`, `parameter_bag`, `Scenarios`, `Spec`,
  `mpt_error_factory`).
- `mpt_extension_contrib.fixtures.factories` — polyfactory `ModelFactory`
  subclasses and the `MPTModelFactory` base.
- `mpt_extension_contrib.fixtures.parameters` — the `parameter_bag` builder.
- `mpt_extension_contrib.fixtures.scenarios` — scenario and parametrization helpers.
- `mpt_extension_contrib.fixtures.errors` — the `mpt_error_factory` helper.
- `mpt_extension_contrib.fixtures.plugin` — the `pytest11` entry-point module
  that registers the convenience fixtures.

## Design boundaries

- Factories build structurally valid SDK models with **empty parameters**.
  Parameter values are product-specific and supplied by the consumer.
- No product-specific business logic, enums, or catalogs live here.
- Platform / MPT-API objects only — never vendor API objects (Adobe, AWS, …).

## SDK models vs the API client

Two object representations exist in the stack, and this library standardises on
the SDK one:

- `mpt_api_client` (the HTTP client, an SDK dependency) returns **dynamic**
  `Model` objects — dicts exposed as attributes — straight from httpx.
- `mpt_extension_sdk.models` are **typed pydantic** models. Every SDK service
  wraps client responses into them via `BaseModel.from_payload(...)`
  (`OrderService.get_by_id` → `Order.from_payload(...)`; `_paginate` →
  `[Model.from_payload(...)]`). Business logic and pipelines only ever see these
  typed models; the client's dynamic representation is an internal transport
  detail.

So the factories build **SDK typed models**. For now, tests **mock at the SDK
service layer** and return a factory model directly — it matches what production
code receives from `from_payload`. `.to_dict()` serialises a model to the exact
camelCase JSON the API returns and is the bridge to any future wire-level mocking;
HTTP/wire mocking helpers are not shipped in this iteration (see Roadmap). No
separate "client model" fixtures are needed.

## Roadmap

Shipped: `OrderFactory` / `AgreementFactory` / `SubscriptionFactory`,
`parameter_bag`, `Scenarios`, `mpt_error_factory`, the pytest plugin.

Planned (MPT-22111 — platform/MPT-API scope only):

- Realistic MPT ids per object (`ORD-####-####-####`, `AGR-…`, `LCE-…`, …) via
  per-factory id providers, propagated into nested models.
- More factories where an SDK model exists: Asset, Account/Buyer/Seller/Licensee,
  Product/Item, Template, Authorization, Price, `ParameterValueFactory` (rich
  parameters with type/phase/constraints), Extension/Installation.
- Event fixtures (`Event` / `TaskEvent` / `EventMetadata`).
- API-response helpers for wire mocking: `api_object`, `api_collection`
  (`{"data": [...], "$meta": {...}}`), `api_error`, plus an optional `respx`
  fixture.
- Depends on SDK follow-ups: models for Listing / Request / PriceList, and
  canonical `OrderType` / `OrderStatus` enums (the SDK still types these as
  `str`).

## Pytest plugin conventions

This package follows the canonical installable-plugin layout
([pytest docs](https://docs.pytest.org/en/stable/how-to/writing_plugins.html),
[`cookiecutter-pytest-plugin`](https://github.com/pytest-dev/cookiecutter-pytest-plugin)):

- **Entry point.** `[project.entry-points.pytest11]` maps a name to
  `mpt_extension_contrib.fixtures.plugin`; pytest auto-discovers the plugin once
  the package is installed — no `conftest.py` wiring for consumers.
- **`plugin.py`.** Holds the fixtures (and would hold hooks such as
  `pytest_configure` / `pytest_addoption` and custom marker registration, if
  any were needed).
- **Package root re-exports the public API** so `from mpt_extension_contrib.fixtures
  import OrderFactory` works.
- **Classifier.** `Framework :: Pytest` is declared so the package is
  discoverable as a pytest plugin on PyPI.
- **Testing.** The plugin is verified the canonical way — with the `pytester`
  fixture running an inline pytest session
  ([test_plugin.py](../tests/test_plugin.py)) — in addition to direct unit tests
  of each helper.
- **Assertion rewriting.** Not used here (no shipped assertion helpers); if a
  helper module ever grows `assert`s for consumers, register it with
  `pytest.register_assert_rewrite(...)`.

### Coverage gotcha (why imports are lazy)

pytest loads the `pytest11` plugin — and everything it imports — during startup,
**before** `pytest-cov` begins instrumentation. On Python 3.12 coverage uses
`sys.monitoring` (PEP 669), which only measures code imported *after* it starts;
anything imported at plugin-load time reads as 0% and cannot be recovered
in-process. To keep the implementation measurable:

- `plugin.py` resolves the implementation lazily (`importlib.import_module`)
  inside each fixture, so factory/helper code is first imported during the test
  session, not at startup.
- `__init__.py` re-exports lazily via a PEP 562 `__getattr__` for the same
  reason. This trips lint rules that expect an eager-re-export `__init__`
  (`ruff` `RUF067`, `flake8`/wemake `WPS412`/`WPS413`); those are intentionally
  ignored for this one file in the root `pyproject.toml`.
- `plugin.py` itself loads at startup and is excluded from coverage
  (`*/plugin.py` in `[tool.coverage.report] omit`); its behaviour is covered by
  the `pytester` test instead.
