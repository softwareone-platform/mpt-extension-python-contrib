# Contributing

Keep the public API under `mpt_extension_contrib.due_date` limited to the
pipeline steps, the `DueDateSettings` protocol, and the `DueDateReachedError`
exception; keep `calculation` and `parameters` internal. Update
[architecture.md](architecture.md) when the public API changes.

Keep the steps free of product-specific business logic: read the parameter
external id from `DueDateSettings` and take the deadline length as a step
argument.

Use package-scoped validation with `pkg=due-date`. Follow the repository-wide
[contributing workflow](../../docs/contributing.md) for dependency changes,
validation commands, and pre-commit expectations.
