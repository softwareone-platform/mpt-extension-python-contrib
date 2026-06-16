# Contributing

Repository-specific rules for the contrib monorepo. Shared engineering standards are
owned by
[`softwareone-platform/mpt-extension-skills`](https://github.com/softwareone-platform/mpt-extension-skills)
— commit messages, pull requests, Python coding, unit tests, packaging, and
documentation conventions live there; the rules below are the repo-local additions.

## Repository rules

- Keep each top-level module independently releasable; do not create a root public
  distribution.
- Never add `mpt_extension_contrib/__init__.py` (see [architecture.md](architecture.md)).
- Put shared tooling config and shared dev tools in the root
  [`pyproject.toml`](../pyproject.toml); put a module's runtime and dev dependencies in
  that module's `pyproject.toml`.
- There is one shared [`uv.lock`](../uv.lock); regenerate and commit it after any
  dependency change.
- Update the matching document when behaviour or workflow changes.

## Adding a module

```bash
make create-module module=<kebab-case-name>
```

This renders the module from [`scripts/templates/module/`](../scripts/templates/module)
(via copier), copies the root `LICENSE`, and auto-wires the module into the workspace —
the root `pyproject.toml` (`members`, pytest `testpaths`, mypy `mypy_path`),
`make/common.mk` `PACKAGES`, and the package tables in the root `README.md` and
`AGENTS.md` — then refreshes `uv.lock`. New modules need no edit to the CI or release
workflows; both derive what they need from the workspace members.

The generated implementation, tests, and module docs are placeholders — replace them
with the real API before the module's first release. Then validate:

```bash
make check-all pkg=<module>
```

Keep scaffold *content* in `scripts/templates/module/` and the repository *wiring* in
[`scripts/scaffold_module.py`](../scripts/scaffold_module.py).

## Validation

Follow the shared
[build-and-checks](https://github.com/softwareone-platform/mpt-extension-skills/blob/main/knowledge/build-and-checks.md)
workflow; the repo command mapping is in [testing.md](testing.md). `make check-all`
runs the structure validator, ruff, flake8, mypy, and pytest inside the shared dev
image so local results match CI. PR CI builds/tests only the modules a change touched.

## Dependencies

Dependabot tracks the root `uv` workspace, `docker`, and `github-actions`
([`dependabot.yml`](../.github/dependabot.yml)). Because the workspace has one shared
`uv.lock`, dependency bumps stay coordinated in a single pull request even though
modules release independently.

## External service setup (per module)

Some integrations are configured outside the repository and are required before a
module's first release / first scan:

- **PyPI** — configure trusted publishing for `mpt-extension-contrib-<module>`; see
  [releases.md](releases.md).
- **SonarCloud** — add the repository secret `SONAR_TOKEN_<MODULE>` (uppercase, with
  hyphens as underscores, e.g. `SONAR_TOKEN_DUE_DATE`). The PR workflow selects it by
  the module's derived name and skips the scan until it exists.

## Releases

See [releases.md](releases.md) for tags, versioning, and the manual release workflow.
