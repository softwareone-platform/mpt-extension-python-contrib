# Architecture

`mpt-extension-contrib-phase-step` provides provisioning-phase gating for
Extension SDK pipeline steps: a step runs only while the order's phase
parameter equals the value the step declares.

## Public API boundary

The package root `mpt_extension_contrib.phase_step` exports only the
integration surface:

```python
from mpt_extension_contrib.phase_step import (
    PhaseGatedStep,
    require_phase,
    advance_phase,
    PhaseStepSettings,
)
```

- `PhaseGatedStep` is an `mpt_extension_sdk` pipeline step (`BaseStep`) whose
  `pre()` skips the step unless the phase matches; subclasses implement
  `process()`. The expected phase is a constructor argument — a single phase
  or a non-empty list of phases.
- `require_phase(context, expected_phases)` is the guard
  `PhaseGatedStep.pre()` calls; it is also available to a step that adds its own
  `pre()`. It reads the phase with `ParameterBag.get_fulfillment_value(...)`.
- `advance_phase(context, phase)` is the write counterpart to gating: it sets
  the phase on an updated `ParameterBag` (`with_fulfillment_value`) and persists
  it through `mpt_api_service`. Steps call it from `process()`; the base class
  never writes the phase itself.
- `PhaseStepSettings` is a `Protocol` declaring the required setting,
  `phase_parameter: str`. Extensions expose this field on `ExtensionSettings`;
  inheriting `PhaseStepSettings` makes the contract explicit and type-checked.

The `steps` module is internal; import from the package root.

## Design

- **Reuse the SDK, do not extend it.** The SDK `BaseStep.run()` awaits `pre()`
  first, and `BasePipeline` already catches `SkipStepError`, logs the skip
  through `on_step_skipped`, and continues with the next step. The whole
  skip-and-continue control flow lives in the SDK, so this library adds only the
  phase-check convention, not a new base pipeline or error type.
- **No decorators, wrappers, or mixins.** Gating is expressed by subclassing
  `PhaseGatedStep` (or calling `require_phase` in a `pre()`). A subclass that
  needs extra `pre()` logic calls `await super().pre(context)` explicitly, so the
  check order is visible in the source instead of resolved by MRO. This keeps the
  facilitation code smaller than the logic it facilitates and preserves each
  step's own `name` for logging and tracing.
- **Phase is bound per instance.** The expected phase is a constructor
  argument (`CreateSubscription("createSubscription")`), so it lives in the
  pipeline definition rather than baked into the class body.
- **Configuration has one source.** The phase parameter external id is read from
  `context.ext_settings.phase_parameter`. No phase vocabulary or parameter id
  is baked into the library — phase values differ per extension and stay in the
  extension.
- **Order snapshots stay immutable.** `advance_phase` never mutates the current
  snapshot in place: it builds a new `ParameterBag` with `with_fulfillment_value(...)`,
  persists it through `context.mpt_api_service.orders.update(...)`, and replaces
  the snapshot only through the sanctioned `context.refresh_order()` (a fresh
  fetch), not by editing `context.order` directly.

## Behaviour

- `PhaseGatedStep(expected_phases)` — `pre()` reads the phase parameter and
  raises `SkipStepError` unless it is one of `expected_phases`; otherwise
  `process()` runs. `expected_phases` is a single phase or a non-empty list of
  non-empty phases, validated at construction.
- `require_phase(context, expected_phases)` — raises `SkipStepError` when the
  current phase (including unset) is not one of `expected_phases`; returns
  `None` on a match.
- `advance_phase(context, phase)` — writes `phase` through
  `context.mpt_api_service.orders.update(...)`, then refreshes `context.order`
  (`context.refresh_order()`) so a later gated step in the same run reads the new
  phase and gates correctly. The caller decides when to call it.

## Out of scope

- Creating or seeding the phase parameter — the extension owns it (see
  [Usage](usage.md)).
- Deciding *when* to advance the phase — `advance_phase` performs the write,
  but the step chooses the moment and the target phase in `process()`.
- Order status transitions such as fail/query/complete (the MPT order status,
  distinct from the provisioning phase this library gates on) — those are
  declared on `context.order_state` and applied by pipeline hooks, per the SDK
  pipeline-steps guideline.
