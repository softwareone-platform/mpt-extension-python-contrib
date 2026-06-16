# Releases

Each top-level module is versioned, published to PyPI, and represented by a
GitHub Release independently, on its own cadence.

## Tags

Module tags use `<module>-<version>`:

```text
shared-1.2.0
due-date-2.0.1
```

The module prefix is what distinguishes tags and GitHub Releases in a repository
that holds several distributions in one git history. Multiple tags may point at
the same commit when modules are released together. The published Python
distribution uses the version *without* the prefix
(`mpt-extension-contrib-shared==1.2.0`); the GitHub Release title adds the
conventional `v` (`mpt-extension-contrib-shared v1.2.0`).

## Package versions

Every module keeps `version = "0.0.0"` in its `pyproject.toml` as a repository
placeholder (enforced by `scripts/check_repository.py`). The release workflow
sets the real version with `uv version` *in the runner checkout only* before
building — the change is never committed. The published version lives in PyPI
and in the `<module>-<version>` git tag.

## Running a release

Trigger the **Release** workflow (`.github/workflows/release.yml`) manually
(`workflow_dispatch`) and supply `packages` as a comma-separated list of
`<module>=<version>` pairs. Several modules can be released in one run:

```text
shared=1.2.0,due-date=2.0.1
```

Versions must be `X.Y.Z`. Unknown modules, duplicates, and malformed tokens are
rejected before anything is built.

For each selected module, in the workspace's declared order, the workflow:

1. Sets the release version with `uv version --package <distribution> <version>`.
2. Builds and verifies the sdist and wheel (`uv build --no-sources`).
3. Creates (or verifies) the annotated tag `<module>-<version>` and pushes it.
4. Publishes the distribution to PyPI via trusted publishing (`uv publish`).
5. Creates the GitHub Release for the tag, attaching the artifacts, with
   **module-scoped notes** — the commits that touched `<module>/` since the
   module's previous release tag. Repository-wide tooling and documentation
   commits are intentionally excluded from a module changelog.

Modules are published **one at a time** (`max-parallel: 1`) so that a shared
dependency reaches PyPI before any module that depends on it, and so the tag and
release pushes never race across runners.

## Re-running

Tags and PyPI uploads are immutable release boundaries. The workflow is
idempotent within those limits: a re-run verifies an existing tag still points
at the same commit and re-uploads release assets with `--clobber`. PyPI will
reject re-publishing a version that already exists — bump the version instead of
reusing one.

## Manual setup (before the first release of a module)

PyPI publishing uses **trusted publishing** (OpenID Connect), so no API token is
stored in the repository. Before a module's first release:

1. Create the PyPI project `mpt-extension-contrib-<module>` (or let the first
   trusted-publishing upload create it, depending on your PyPI org policy).
2. On PyPI, add a **trusted publisher** for the project pointing at this
   repository and the `release.yml` workflow.

Until that is configured, the `Publish to PyPI` step of a triggered release will
fail; the build, tag, and release-notes steps do not require it.
