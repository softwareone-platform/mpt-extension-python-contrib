# Contributing

Keep the public API under `mpt_extension_contrib.phase_step` limited to
`PhaseGatedStep`, `require_phase`, `advance_phase`, and the
`PhaseStepSettings` protocol. Import them from the package root; the `steps`
submodule is implementation detail. Update
[architecture.md](architecture.md) when the public API changes.

Keep the library free of product-specific phase values and parameter ids:
the expected phases are constructor/argument input, and the phase parameter
external id comes from `PhaseStepSettings` (`context.ext_settings`). Do not add
a phase enum, a default parameter name, or any extension business logic.

Do not reimplement the pipeline control flow. Skipping relies on the SDK: raise
`SkipStepError` from a `pre()` hook and let `BasePipeline` log and continue. A
step that also needs its own `pre()` calls `await super().pre(context)` first;
prefer this explicit subclassing over decorators, wrappers, or mixins.

Use package-scoped validation with `pkg=phase-step`. Follow the
repository-wide [contributing workflow](../../docs/contributing.md) for
dependency changes, validation commands, and pre-commit expectations.
