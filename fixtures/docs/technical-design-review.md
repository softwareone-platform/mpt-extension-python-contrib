# Technical Design Review — MPT pytest fixtures (MPT-22111)

Status: proposed · Scope: platform / MPT-API test fixtures · Owner: _TBD (CODEOWNERS)_

This document states the problems we want to solve and the requirements the
`mpt-extension-contrib-fixtures` module must meet, and points at the worked
examples in [usage.md](usage.md) and the design in
[architecture.md](architecture.md).

## Context

Every MPT extension re-implements the same test data by hand. A survey of the
suites showed heavy, divergent copies of MPT object factories:

- **adobe** (`swo-adobe-vipm-extension`) — ~25 generic MPT fixtures, ~2000+ dict-key
  accesses across ~50 test files.
- **aws** (`swo-aws-extension`) — ~15 generic fixtures, `mpt_error_factory` copied
  verbatim, parameter factories tied to product enums.
- **adobe-ef**, **aws-usage** — flat `agreement_payload` dicts (auth / billing
  domains, largely orthogonal).
- **installations** — already on typed SDK models, but needs context/mocks.

Each copy drifts from the real API shape, mixes product-specific values into
platform structure, and duplicates the same error/parameter/enum helpers.

## Problems to solve

1. **Duplication.** The same MPT object builders (order, agreement, subscription,
   buyer, seller, licensee, listing, parameters, errors) are re-authored per repo.
2. **Untyped drift.** Factories return raw dicts with hand-maintained camelCase
   keys, disconnected from the SDK models and the real API payload shape.
3. **Parameter coupling.** Product-specific parameter catalogs are baked into the
   structural fixtures — two different axes (platform/status vs consumer catalog)
   are tangled together.
4. **Reinvented parametrization.** Scenario/matrix testing is re-built per repo,
   per entity.
5. **Two representations.** The dynamic `mpt_api_client` model and the typed SDK
   model coexist, and it is unclear which one to build in tests.

## Requirements

Functional:

- R1 — Reusable factories for MPT-shaped objects, installable as a package, public
  API under `mpt_extension_contrib.fixtures`.
- R2 — **Platform / MPT-API objects only.** No vendor (Adobe/AWS) API objects and
  no product-specific business logic, enums, or parameter catalogs.
- R3 — Parameters are consumer-owned; the library provides structure and injection
  seams, not values.
- R4 — One parametrization primitive that works for any entity.
- R5 — Mocking is done at the **SDK layer only** for now: a mocked SDK service
  returns a typed factory model. HTTP/wire-level mocking helpers are out of scope
  for this iteration.
- R6 — Realistic MPT identifiers per object type (`ORD-…`, `AGR-…`, `LCE-…`).

Non-functional:

- R7 — Compatible with Extension SDK ≥ 6.0; factories build the SDK's typed models.
- R8 — Minimum dependencies; no cross-module dependencies.
- R9 — Unit tests with coverage per repo standard (95%+); lint/type clean.
- R10 — Self-discoverable docs and an explicit owner (CODEOWNERS); published to PyPI.

## How the module addresses this

- **Typed SDK-model factories (problems 1, 2; R1, R7).** polyfactory `ModelFactory`
  subclasses build the SDK's typed `Order` / `Agreement` / `Subscription` with
  empty parameters — see [Building models](usage.md#building-models). This removes
  the per-repo dict copies and keeps a single typed source of truth.
- **Consumer-owned parameters (problem 3; R3).** Factories default to empty
  parameters. The consumer injects a catalog with `parameter_bag`, a build
  override, or a factory subclass; the platform axis (order-type presets) is kept
  separate from the consumer catalog — see
  [Injecting parameters](usage.md#injecting-parameters-the-consumer-axis) and
  [Predefined scenarios](usage.md#predefined-scenarios-not-random).
- **One parametrization primitive (problem 4; R4).** `Scenarios(factory, {...})`
  works for any entity via `.build()` / `.cases()` / `.fixture()`. A spec is a
  plain set of factory field overrides — it can vary any field (status, type,
  lines, subscriptions, parameters, ...); parameters are not special-cased. See
  [Named scenarios](usage.md#named-scenarios-scenarios).
- **Shared error helper (problem 1).** `mpt_error_factory` — see
  [MPT error payloads](usage.md#mpt-error-payloads).
- **One representation, SDK-level mocking (problem 5; R5).** The library
  standardises on the typed SDK model. Tests mock the SDK service and return a
  factory model directly. The SDK already wraps every API response into a typed
  model via `from_payload`, so this matches production; the boundary is described
  in [SDK vs API client](architecture.md#sdk-models-vs-the-api-client). `.to_dict()`
  is documented as the bridge to the API JSON shape for the future wire-mocking
  helpers, but those are not part of this iteration.
- **Zero-wiring adoption (R1).** Ships as a pytest plugin via the `pytest11` entry
  point — see [Fixtures provided by the plugin](usage.md#fixtures-provided-by-the-plugin)
  and [plugin conventions](architecture.md#pytest-plugin-conventions).
- **Coverage on a startup-loaded plugin (R9).** Lazy plugin/package init keeps
  plugin-startup imports measurable on Python 3.12 — see
  [Coverage gotcha](architecture.md#coverage-gotcha-why-imports-are-lazy).
- **Demo.** An Order/Agreement [demo test](../tests/test_demo.py) uses the fixtures
  in a passing suite.

## Non-goals

- Vendor API objects (Adobe/AWS), product-specific parameter values and enums.
- HTTP/wire-level API mocking helpers (e.g. `respx`) — mocking is done at the SDK
  service layer for now.
- Pipeline contexts with service mocks, and billing/auth domains.

See [Design boundaries](architecture.md#design-boundaries).

## Open questions & follow-ups

- **R6 — id generation** is on the roadmap ([Roadmap](architecture.md#roadmap));
  confirm the Licensee prefix (`LCE-` per platform docs vs `LIC-` in current SDK tests).
- **Enums.** Canonical `OrderType` / `OrderStatus` should live in the SDK (it still
  types these as `str`); this library keeps strings until then.
- **Missing SDK models.** Listing / Request / PriceList have no SDK model yet —
  needed before fixtures can build them.
- **Later iterations.** Expanded factory set (Asset, Account/Buyer/Seller/Licensee,
  Product/Item, Template, Authorization, Price, `ParameterValueFactory`), Event
  fixtures, and — only if a real need appears — wire-level API-response mocking helpers.
- **R10** — assign CODEOWNERS and cut the first PyPI release.
