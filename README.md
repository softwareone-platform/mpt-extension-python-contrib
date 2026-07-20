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
| `order-status/` | `mpt-extension-contrib-order-status` | `mpt_extension_contrib.order_status` | public |
| `phase-step/` | `mpt-extension-contrib-phase-step` | `mpt_extension_contrib.phase_step` | public |
| `custom-notifications/` | `mpt-extension-contrib-custom-notifications` | `mpt_extension_contrib.custom_notifications` | public |
| `reports/` | `mpt-extension-contrib-reports` | `mpt_extension_contrib.reports` | public |
| `due-date/` | `mpt-extension-contrib-due-date` | `mpt_extension_contrib.due_date` | public |

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

Everything runs through `make` inside a shared Docker image, so local results match
CI:

```bash
make build         # build the dev image (after changing uv.lock)
make check-all     # repo-check + ruff + flake8 + mypy + pytest (pkg=<module> to scope)
make format        # auto-format with ruff
```

Full setup, dependency, non-Docker, and module-scaffold commands are in
[docs/local-development.md](docs/local-development.md). CI builds/tests only the
packages a change touched; releases are per module — see
[docs/releases.md](docs/releases.md).

## Adding a module

```bash
make create-module module=<kebab-case-name>
```

Renders the module, copies the `LICENSE`, and **auto-wires** it into the workspace
(`members`, `PACKAGES`, pytest/mypy paths, the README/AGENTS tables), then refreshes
`uv.lock`. See [docs/contributing.md](docs/contributing.md).

## Documentation

- [AGENTS.md](AGENTS.md): entry point and working protocol for contributors and AI
  agents.
- [docs/architecture.md](docs/architecture.md): repository model, namespace invariant,
  and release model.
- [docs/contributing.md](docs/contributing.md): repository rules, adding a module, and
  per-module external setup.
- [docs/local-development.md](docs/local-development.md): local setup, the `make`
  workflow, dependency commands, and scaffolding.
- [docs/releases.md](docs/releases.md): how to release a module (tags, versions,
  the Release workflow, and PyPI setup).
- [docs/testing.md](docs/testing.md): testing strategy and command mapping.
- [docs/documentation.md](docs/documentation.md): documentation rules and the full
  documentation map.
