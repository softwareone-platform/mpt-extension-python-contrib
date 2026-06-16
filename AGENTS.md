# AGENTS.md

Working protocol for any task in this repository:

1. Identify the package or repository-level concern affected by the task.
2. Read only the relevant local files before making changes.
3. Read the matching shared standard or operational guidance from
   [`softwareone-platform/mpt-extension-skills`](https://github.com/softwareone-platform/mpt-extension-skills)
   when the task involves shared engineering conventions.
4. Treat repository-local documents as additions, restrictions, or overrides to
   shared guidance.

## Repository model

`mpt-extension-contrib` is a [uv](https://docs.astral.sh/uv/) **workspace monorepo**
of independently released Python libraries for SoftwareONE MPT extensions. It does
not publish an umbrella `mpt-extension-contrib` distribution.

- The root [`pyproject.toml`](pyproject.toml) defines the uv workspace and the shared
  tool configuration (ruff, flake8, mypy, pytest, coverage). It is **not** an
  installable distribution.
- A single [`uv.lock`](uv.lock) at the repository root locks the whole workspace.
- Each root-level directory is one distribution. All distributions share the
  **PEP 420 namespace package** `mpt_extension_contrib`.

Mechanical naming rule for a module `<module>`:

```text
Repository directory: <module>                          (kebab-case)
Distribution name:    mpt-extension-contrib-<module>
Python import:        mpt_extension_contrib.<module_with_underscores>
```

## Packages

- [`shared/`](shared): internal reusable code exposed as `mpt_extension_contrib.shared`
  (distribution `mpt-extension-contrib-shared`).

## Operational guidance

- Keep `mpt_extension_contrib` a namespace package. Never add
  `mpt_extension_contrib/__init__.py` at the namespace root; only a concrete module
  directory (for example `mpt_extension_contrib/shared/`) owns an `__init__.py`. A
  namespace-level `__init__.py` would shadow sibling distributions when several
  contrib packages are installed together.
- Keep each root-level package independently releasable.
- Add shared development tools to the root `pyproject.toml`.
- Add package-specific runtime and development dependencies to the matching package
  `pyproject.toml`.
- Keep one workspace lockfile: regenerate `uv.lock` with `uv lock` and commit it.
- Do not invent release, compatibility, or testing guarantees that are not
  represented in repository code or documentation.

> Repository tooling (make targets, Docker development image, CI workflows), the
> release pipeline, and per-module documentation are being introduced incrementally
> by the Foundation stories and are not all present yet.
