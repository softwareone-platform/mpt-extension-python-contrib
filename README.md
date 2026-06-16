# MPT Extension Contrib

`mpt-extension-contrib` is a monorepo for shared Python libraries used by SoftwareONE
MPT extensions.

The repository does not publish an umbrella `mpt-extension-contrib` package. Each
root-level package directory is an independently released Python distribution, and all
of them share the `mpt_extension_contrib` namespace.

## Packages

| Directory | Distribution | Python import | Visibility |
| --- | --- | --- | --- |
| `shared/` | `mpt-extension-contrib-shared` | `mpt_extension_contrib.shared` | internal |

## Naming rule

For a module `<module>`:

```text
Repository directory: <module>                          (kebab-case)
Distribution name:    mpt-extension-contrib-<module>
Python import:        mpt_extension_contrib.<module_with_underscores>
```

## Repository structure

```text
mpt-extension-contrib/
├── pyproject.toml          # uv workspace + shared tool config (NOT a distribution)
├── uv.lock                 # single lockfile for the whole workspace
├── shared/                 # a module → mpt-extension-contrib-shared
│   ├── pyproject.toml
│   ├── mpt_extension_contrib/shared/   # namespace package (no root __init__.py)
│   └── tests/
├── due-date/               # another module (same shape)
├── scripts/                # repository tooling (scaffold, validate, detect, release)
│   └── templates/module/   # copier template for `make create-module`
├── make/                   # canonical `make` targets, run inside the dev image
├── docs/                   # repository-level documentation
├── Dockerfile              # shared dev image
└── .github/workflows/      # changed-only CI + manual release
```

## Two views

The repository has two views of the same code:

```text
ON DISK (workspace)                 INSTALLED (a consumer's environment)
mpt-extension-contrib/              site-packages/
├── shared/                         └── mpt_extension_contrib/    ◄── PEP 420 namespace
│   └── mpt_extension_contrib/          │                            (NO __init__.py here)
│       └── shared/                     ├── shared/      ◄─ from ...-shared
└── due-date/                           └── due_date/    ◄─ from ...-due-date
    └── mpt_extension_contrib/
        └── due_date/
```

On disk it is a workspace of sibling directories. Once installed, the distributions
merge under one `mpt_extension_contrib.*` import root — because the namespace package
has **no root `__init__.py`**, several contrib packages coexist in the same
environment without shadowing each other (the normal case for a consumer extension
that installs only the modules it needs).

## Development

This repository is a [uv](https://docs.astral.sh/uv/) workspace (Python 3.12).

```bash
uv sync --all-packages --all-groups   # create the workspace environment
uv lock --check                       # verify the lockfile is current
uv run ruff check .                   # lint
uv run ruff format --check .          # formatting
uv run flake8 .                       # wemake style checks
uv run mypy .                         # type checking
```

A `make` toolchain runs the same checks inside a shared Docker image (so local
results match CI):

```bash
make check-all              # repo-check + ruff + flake8 + mypy + pytest for all packages
make check pkg=<module>     # scope checks to one package
make format                 # auto-format with ruff
make repo-check             # validate workspace package structure (run by `make check`)
```

CI runs the same checks on every PR, building/testing only the packages a change
touched (`.github/workflows/pr-build-merge.yml`). Releases are published per module
through a manual workflow — see [docs/releases.md](docs/releases.md).

## Adding a module

Scaffold a new contrib distribution from the template:

```bash
make create-module module=<kebab-case-name>
```

This renders `<module>/` from `scripts/templates/module` (via
[copier](https://copier.readthedocs.io/)), copies the repository `LICENSE` into
it, and **auto-wires** the module into the workspace — the root `pyproject.toml`
(`members`, pytest `testpaths`, mypy `mypy_path`), `make/common.mk` `PACKAGES`,
and the package tables in `README.md` and `AGENTS.md` — then refreshes
`uv.lock`.

## Documentation

- [AGENTS.md](AGENTS.md): entry point and working protocol for contributors and AI
  agents.
- [docs/releases.md](docs/releases.md): how to release a module (tags, versions,
  the Release workflow, and PyPI setup).
