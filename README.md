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

On disk the repository is a workspace of sibling directories. Once installed, the
distributions merge under one `mpt_extension_contrib.*` import root because the
namespace package has no root `__init__.py`, so multiple contrib packages can coexist
in the same environment.

## Layout

- `pyproject.toml` — uv workspace and shared tool configuration; not an installable
  distribution.
- `uv.lock` — single lockfile for the whole workspace.
- `shared/` — first workspace package.

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

> Make targets, a Docker-based development image, CI workflows, and the release
> pipeline are being added by subsequent Foundation stories.

## Documentation

- [AGENTS.md](AGENTS.md): entry point and working protocol for contributors and AI
  agents.
