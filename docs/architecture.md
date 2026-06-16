# Architecture

`mpt-extension-contrib` is a [uv](https://docs.astral.sh/uv/) **workspace monorepo**
of independently released Python libraries for SoftwareONE MPT extensions.

## Repository model

- The root [`pyproject.toml`](../pyproject.toml) defines the uv workspace and the
  shared tool configuration (ruff, flake8, mypy, pytest, coverage). It is **not** an
  installable distribution — there is no umbrella `mpt-extension-contrib` package.
- A single [`uv.lock`](../uv.lock) locks the whole workspace.
- Each top-level directory is one independently released distribution. The live list
  of packages is the package table in the root [`README.md`](../README.md) (kept in
  sync by `make create-module`).

## Naming rule

For a module `<module>`:

```text
Repository directory: <module>                          (kebab-case)
Distribution name:    mpt-extension-contrib-<module>
Python import:        mpt_extension_contrib.<module_with_underscores>
```

Directories and distribution names use hyphens; the Python import segment uses
underscores.

## Namespace package

All distributions share the **PEP 420 namespace package** `mpt_extension_contrib`.
No distribution may contain `mpt_extension_contrib/__init__.py` — that file would
claim the namespace and shadow sibling distributions installed alongside it. Only a
concrete module directory owns an `__init__.py`, e.g. `mpt_extension_contrib/shared/`.

This invariant is enforced two ways:

- [`scripts/check_repository.py`](../scripts/check_repository.py) (run by
  `make check` / `make repo-check`) fails if a namespace-root `__init__.py` exists.
- [`tests/test_namespace.py`](../tests/test_namespace.py) asserts the installed
  packages coexist under one namespace root.

See the "Two views" section of the [README](../README.md) for the on-disk vs
installed picture.

## The `shared` module

[`shared/`](../shared) (`mpt-extension-contrib-shared`) holds internal helpers reused
by other contrib modules. It is internal API: extension repositories should not depend
on it directly. It is released independently, and a breaking change to `shared` does
not require updating every consumer in the same change — consumers bump their declared
`mpt-extension-contrib-shared` constraint when they adopt a new release.

## Release model

Each distribution is versioned and released independently:

- a change limited to one module releases only that module;
- a compatible change to `shared` is released before any consumer that needs it
  (the release workflow publishes in workspace order, one module at a time).

Git tags use `<module>-<version>`; each module gets its own GitHub Release. See
[releases.md](releases.md).

## CI

The PR workflow ([`.github/workflows/pr-build-merge.yml`](../.github/workflows/pr-build-merge.yml))
classifies changed files with
[`scripts/detect_changed_packages.py`](../scripts/detect_changed_packages.py) and
builds/tests only the affected modules; a change to shared tooling fans out to every
module. See [contributing.md](contributing.md) and [testing.md](testing.md).
