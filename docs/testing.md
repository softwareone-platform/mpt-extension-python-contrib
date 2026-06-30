# Testing

Shared testing and validation guidance is owned by
[`mpt-extension-skills`](https://github.com/softwareone-platform/mpt-extension-skills):

- [standards/unittests.md](https://github.com/softwareone-platform/mpt-extension-skills/blob/main/standards/unittests.md)
- [knowledge/build-and-checks.md](https://github.com/softwareone-platform/mpt-extension-skills/blob/main/knowledge/build-and-checks.md)
- [knowledge/make-targets.md](https://github.com/softwareone-platform/mpt-extension-skills/blob/main/knowledge/make-targets.md)

This file documents repository-specific test behaviour only.

## Test scope

Each independently released package owns its tests in a local `tests/` directory,
plus the repository-level suites:

```text
tests/              # workspace-wide checks (namespace coexistence)
scripts/tests/      # repository tooling (scaffold, validate, detect, release)
shared/tests/
due-date/tests/
order-status/tests/
```

Tests cover the public behaviour of the affected package. A change to `shared` must
cover its helper behaviour. Coverage is measured for the `mpt_extension_contrib`
namespace and is **hard-enforced at 95%** (`--cov-fail-under=95` in the root
`pyproject.toml`): `make test` fails when coverage drops below the threshold. Because
a scoped run installs only the target module, the threshold applies per module under
`pkg=<module>` and across the whole namespace for a full run.

## Shared test fixtures

Generic Extension SDK fixtures live in
[`tests/fixtures/sdk.py`](../tests/fixtures/sdk.py) and are registered globally via
`pytest_plugins` in the root [`conftest.py`](../conftest.py), so every module's tests
can request them by name:

| Fixture | Provides |
| --- | --- |
| `parameter_bag_factory(ordering=…, fulfillment=…)` | a `ParameterBag` from lists of `ParameterValue` |
| `event_metadata` | a real `EventMetadata` |
| `runtime_settings` | a real `RuntimeSettings` |
| `mpt_api_service` | a real `MPTAPIService` whose `orders` service is autospec'd |
| `order_context_factory(ordering=…, fulfillment=…)` | a real `OrderContext` built from the fixtures above |

`order_context_factory` depends on an `extension_settings` fixture that each module
provides in its own `tests/conftest.py` (the module's `ExtensionSettings` instance), so
the built context carries that module's settings. Keep module-specific value builders
in the module conftest too (for example due-date's `due_date_parameter_factory`).

Prefer these fixtures over constructing SDK objects by hand:

```python
async def test_my_step(order_context_factory):
    context = order_context_factory(fulfillment=[...])

    await MyStep().run(context)

    ...
```

Keep the shared fixtures generic (no product specifics) so other modules can reuse
them; module-specific builders belong in the module's `tests/conftest.py`.

## Commands

All checks run inside the shared dev image, so local results match CI:

- `make check` — repository structure validation (`scripts/check_repository.py`),
  `ruff format --check`, `ruff check`, `flake8` (wemake), `mypy`, and `uv lock --check`.
- `make test` — `pytest` with coverage; fails under the 95% threshold.
- `make check-all` — both of the above.
- Add `pkg=<module>` to scope `check`/`test` to one package; without it the full
  workspace (and the repo-level `tests/`) is checked.

Pytest settings come from the root [`pyproject.toml`](../pyproject.toml): tests are
discovered under the configured `testpaths`, coverage targets `mpt_extension_contrib`,
and tests run with `--import-mode=importlib`.

## Invariants validated

- **Namespace** — `scripts/check_repository.py` fails if any package adds a
  namespace-root `mpt_extension_contrib/__init__.py`, and
  [`tests/test_namespace.py`](../tests/test_namespace.py) asserts the installed
  distributions coexist under one `mpt_extension_contrib.*` root.
- **Structure** — `make repo-check` (run by `make check`) validates that the root
  `pyproject.toml` stays workspace-only and that every member has `LICENSE`,
  `README.md`, `AGENTS.md`, `docs/`, `pyproject.toml`, `tests/`, the placeholder
  version `0.0.0`, a concrete module `__init__.py`, and a PEP 561 `py.typed` marker
  so consumers' type checkers honour the shipped annotations.

## Pull request CI

[`.github/workflows/pr-build-merge.yml`](../.github/workflows/pr-build-merge.yml) runs
on pull requests and pushes to `main`. It detects affected modules from the changed
paths ([`scripts/detect_changed_packages.py`](../scripts/detect_changed_packages.py))
and builds/tests only those:

- a change inside one module builds/tests that module only;
- a change to shared tooling (root `pyproject.toml`, `uv.lock`, `scripts/`, `make/`,
  `.github/`, …) builds/tests every module;
- a docs-only change runs structure validation without starting the package matrix.

A separate `sonar` job runs one SonarCloud scan for the whole repository, using the
root [`sonar-project.properties`](../sonar-project.properties) (a single project, so
it works on the SonarCloud free plan). Coverage is intentionally not reported to
SonarCloud — it is enforced locally by the 95% test threshold instead. The scan is
skipped until the single `SONAR_TOKEN` secret is configured (see
[contributing.md](contributing.md)).
