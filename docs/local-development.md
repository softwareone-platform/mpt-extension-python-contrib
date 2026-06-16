# Local development

The shared `make`/build flow is documented in
[knowledge/build-and-checks.md](https://github.com/softwareone-platform/mpt-extension-skills/blob/main/knowledge/build-and-checks.md)
and [knowledge/make-targets.md](https://github.com/softwareone-platform/mpt-extension-skills/blob/main/knowledge/make-targets.md).
This file covers the repository-specific local workflow.

## Prerequisites

- Docker with the `docker compose` plugin — the default execution model.
- Python 3.12 (see [`.python-version`](../.python-version)).
- [uv](https://docs.astral.sh/uv/) — only for running tools outside Docker.

## Docker workflow (default)

Every `make` target runs inside one shared image, so local results match CI.

```bash
make build                  # build the dev image (after changing uv.lock)
make check-all              # repo-check + ruff + flake8 + mypy + pytest, all packages
make check pkg=<module>     # scope checks to one package
make test pkg=<module>      # scope tests to one package
make format                 # ruff import-sort + format
make bash                   # open a shell in the dev image
make down                   # stop and remove containers
```

`make check` runs the repository structure validator, `ruff format --check`,
`ruff check`, `flake8` (wemake), `mypy`, and `uv lock --check`; `make test` runs
`pytest` with coverage. See [testing.md](testing.md) for the test details.

## Adding a module

```bash
make create-module module=<kebab-case-name>
```

This renders the module from the copier template, copies the `LICENSE`, and auto-wires
it into the workspace, then refreshes `uv.lock`. Replace the generated placeholder
code, then `make check-all pkg=<module>`. See [contributing.md](contributing.md) for
the full workflow and the per-module external setup.

## Managing dependencies

Use the `make` targets so the module `pyproject.toml` and the shared `uv.lock` stay in
sync:

```bash
make uv-add dep=<dep>            # runtime dep at the workspace (or pkg=<module>)
make uv-add-dev dep=<dep>        # dev dep (pkg=<module> to scope to one package)
make uv-add pkg=<module> dep=<dep>
make uv-upgrade                  # refresh the lockfile (dep=<name> for one)
```

## Without Docker

The same checks can run directly against a local uv environment — useful for quick
edits, though Docker is the source of truth:

```bash
uv sync --all-packages --all-groups
uv run ruff check .
uv run flake8 .
uv run mypy .
uv run pytest
uv lock --check
```
