# AGENTS.md

Working protocol for any task in this repository:

1. Identify the package or repository-level concern affected by the task.
2. Read only the relevant local files before making changes.
3. Read the matching shared standard or operational guidance from
   [`softwareone-platform/mpt-extension-skills`](https://github.com/softwareone-platform/mpt-extension-skills)
   when the task involves shared engineering conventions (resolved locally from
   `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current`).
4. Treat repository-local documents as additions, restrictions, or overrides to
   shared guidance.
5. If a repository-local rule conflicts with a shared or global rule, the
   repository-local rule takes precedence.

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
- [`custom-notifications/`](custom-notifications): public package exposed as `mpt_extension_contrib.custom_notifications` (distribution `mpt-extension-contrib-custom-notifications`).
- [`due-date/`](due-date): public package exposed as `mpt_extension_contrib.due_date` (distribution `mpt-extension-contrib-due-date`).

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

## Read in this order

1. [README.md](README.md) — purpose, repository structure, the two-view model, the
   naming rule, and the `make` workflow.
2. [docs/architecture.md](docs/architecture.md) — repository model, the namespace
   invariant, and the release model.
3. [docs/contributing.md](docs/contributing.md) — before changing dependencies,
   adding a module, or preparing a pull request.
4. [docs/local-development.md](docs/local-development.md) — for the local `make`
   workflow, dependency commands, and scaffolding.
5. [docs/testing.md](docs/testing.md) — before changing code or tests.
6. [docs/releases.md](docs/releases.md) — before tagging or publishing a module.
7. [docs/documentation.md](docs/documentation.md) — when changing repository
   documentation; it also holds the full documentation map.

Shared engineering standards (commit messages, pull requests, Python coding, unit
tests, packaging, make targets) live in
[`mpt-extension-skills`](https://github.com/softwareone-platform/mpt-extension-skills);
the documents above link to the relevant shared standard and override it only where
stated.

Then the code and tooling:

- [`make/`](make): canonical commands; prefer them over ad hoc `uv`/Docker calls.
- [`scripts/`](scripts): repository tooling (`scaffold_module.py`,
  `check_repository.py`, `detect_changed_packages.py`, `prepare_release.py`).
- [`.github/workflows/`](.github/workflows): changed-only PR CI and the manual
  release workflow.
