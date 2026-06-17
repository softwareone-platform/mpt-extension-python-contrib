# Architecture

`mpt-extension-contrib-due-date` provides order processing due-date handling as
Extension SDK pipeline steps.

## Public API boundary

The package root `mpt_extension_contrib.due_date` exports only the integration
surface:

```python
from mpt_extension_contrib.due_date import (
    SetDueDate,
    EnforceDueDate,
    ResetDueDate,
    DueDateSettings,
    DueDateReachedError,
)
```

- `SetDueDate`, `EnforceDueDate`, `ResetDueDate` are `mpt_extension_sdk` pipeline
  steps (`BaseStep`) operating on an `OrderContext`.
- `DueDateSettings` is a `Protocol` declaring the required setting,
  `due_date_parameter: str`. Extensions that use the due-date steps must expose
  this field on `ExtensionSettings`; inheriting `DueDateSettings` is the
  recommended way to make that contract explicit and type-checked.
- `DueDateReachedError` is the `StopStepError` subclass `EnforceDueDate` raises,
  so a pipeline hook can recognise a due-date failure (`isinstance`).

The `calculation` and `parameters` modules are **internal** implementation
details and are not part of the public API.

## Design

- **Configuration has one source.** The due-date parameter external id is read
  from `context.ext_settings.due_date_parameter`; the deadline length is the
  `SetDueDate(days=...)` argument. No product-specific constants are baked in.
- **Single responsibility per step.** Setting/persisting, enforcing, and
  resetting the due date are separate steps so they can be placed independently
  in a pipeline.
- **Order snapshots stay immutable.** Steps never mutate or reassign
  `context.order`. They build the new parameters with the immutable
  `ParameterBag` helpers and persist them through
  `context.mpt_api_service.orders.update(...)`. `SetDueDate` is decorated with
  `@refresh_order` so the context order reflects the persisted due date for
  later steps.
- **Transitions go through pipeline hooks.** `EnforceDueDate` does not fail the
  order itself. It records the intent on `context.order_state.action`
  (`OrderStatusActionType.FAIL`) and raises `StopStepError`; the extension's
  pipeline applies it in an `on_step_stopped` / `on_step_failed` hook, per the
  SDK pipeline-hooks contract.

## Behaviour

Each step decides in `pre()` whether it has work to do and raises `SkipStepError`
otherwise, so the pipeline records a skip instead of running a no-op.

- `SetDueDate(days=N)` — skipped once the due date is set; otherwise persists
  `today + N` days on the order and refreshes the context, keeping the deadline
  stable across reprocessing.
- `EnforceDueDate()` — skipped while the due date is unset; once it has passed,
  records a `Failed` action on `context.order_state` and stops the pipeline; a
  no-op while it is still in the future.
- `ResetDueDate()` — skipped when already unset; otherwise persists a cleared due
  date. Run it before completing an order to leave a clean state.
