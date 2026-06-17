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
```

Tests cover the public behaviour of the affected package. A change to `shared` must
cover its helper behaviour. Coverage is measured for the `mpt_extension_contrib`
namespace and is **hard-enforced at 95%** (`--cov-fail-under=95` in the root
`pyproject.toml`): `make test` fails when coverage drops below the threshold. Because
a scoped run installs only the target module, the threshold applies per module under
`pkg=<module>` and across the whole namespace for a full run.

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
  version `0.0.0`, and a concrete module `__init__.py`.

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
