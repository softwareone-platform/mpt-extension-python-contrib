# Documentation

This repository follows the shared documentation standard:

- [standards/documentation.md](https://github.com/softwareone-platform/mpt-extension-skills/blob/main/standards/documentation.md)

The canonical engineering standards and operational knowledge live in
[`softwareone-platform/mpt-extension-skills`](https://github.com/softwareone-platform/mpt-extension-skills)
— commit messages, pull requests, Python coding, unit tests, packaging, make targets,
and the build-and-checks flow. Repository documents link to those and only describe
repository-specific behaviour. (Agents resolve the shared docs locally from
`${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current`.)

## Repository rules

- `README.md` stays short — the human entry point: purpose, structure, quick start,
  and the documentation map.
- `AGENTS.md` stays operational — it tells AI agents which files to read first.
- Topic-specific behaviour lives in the matching file under [`docs/`](.).
- `.github/copilot-instructions.md` stays a thin adapter that points back to
  [`AGENTS.md`](../AGENTS.md).
- When behaviour or workflow changes, update the matching document in the same change;
  prefer updating the smallest relevant document over adding overlapping summaries.
- Repository-level docs (here) describe the workspace; each module's own `docs/`
  describes that single module.

## Documentation map

- [`README.md`](../README.md): purpose, repository structure, the two-view model,
  the naming rule, and quick start
- [`AGENTS.md`](../AGENTS.md): AI entry point and "where things live"
- [`architecture.md`](architecture.md): repository model, namespace invariant, and
  release model
- [`contributing.md`](contributing.md): repository rules, adding a module, validation,
  and per-module external setup
- [`releases.md`](releases.md): tags, versioning, and the manual release workflow
- [`testing.md`](testing.md): testing strategy and the command mapping
