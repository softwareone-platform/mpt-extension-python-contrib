# Usage

This guide covers installing the library, configuring the due-date parameter,
adding the steps to a pipeline, and failing the order when the deadline passes.

## 1. Install

```bash
pip install mpt-extension-contrib-due-date
```

Requires the Extension SDK (`mpt-extension-sdk >= 6.3, < 7`), pulled in as a
dependency.

## 2. Configure the due-date parameter

The steps read the due-date parameter external id from
`context.ext_settings.due_date_parameter`. Inherit `DueDateSettings` on the
extension settings so the contract is type-checked:

```python
from dataclasses import dataclass
from typing import Self, override

from mpt_extension_sdk.settings.extension import BaseExtensionSettings

from mpt_extension_contrib.due_date import DueDateSettings


@dataclass(frozen=True)
class ExtensionSettings(BaseExtensionSettings, DueDateSettings):
    due_date_parameter: str = "dueDate"

    @override
    @classmethod
    def load(cls) -> Self:
        return cls()
```

## 3. Add the steps to a pipeline

The deadline length is the `SetDueDate(days=...)` argument; the steps read the
parameter external id from the settings above.

```python
from mpt_extension_sdk.pipeline import BasePipeline, BaseStep

from mpt_extension_contrib.due_date import EnforceDueDate, ResetDueDate, SetDueDate


class PurchasePipeline(BasePipeline):
    @property
    def steps(self) -> list[BaseStep]:
        return [
            SetDueDate(days=14),  # assign the deadline on first run
            EnforceDueDate(),  # stop the order once the deadline passes
            # ... order processing steps ...
            ResetDueDate(),  # clear the deadline before completing
        ]
```

- `SetDueDate(days=N)` — persists `today + N` days once; skipped when the due
  date is already set, so the deadline is stable across reprocessing.
- `EnforceDueDate()` — skipped while the due date is unset; once it has passed,
  records a `Failed` action and stops the pipeline; a no-op while still in the
  future.
- `ResetDueDate()` — clears the due date; run it before completing the order.

## 4. Fail the order when the deadline passes

`EnforceDueDate` does not fail the order itself: it records the intent on
`context.order_state.action` and raises `DueDateReachedError` (a `StopStepError`
subclass). Following the SDK pipeline-hooks contract, the extension's pipeline
applies the action in an `on_step_stopped` / `on_step_failed` hook:

```python
from mpt_extension_sdk.errors.step import StopStepError
from mpt_extension_sdk.pipeline import BasePipeline, OrderStatusActionType

from mpt_extension_contrib.due_date import DueDateReachedError


class OrderPipeline(BasePipeline):
    async def on_step_stopped(self, step, ctx, error: StopStepError) -> None:
        await super().on_step_stopped(step, ctx, error)
        action = ctx.order_state.action
        if action and not ctx.order_state.handled:
            if action.target_status == OrderStatusActionType.FAIL:
                await ctx.mpt_api_service.orders.fail(ctx.order_id, action.status_notes)
            ctx.order_state.handled = True
```

`EnforceDueDate` raises `DueDateReachedError` (a `StopStepError`), so
`on_step_stopped` is the hook that applies its action. Implement `on_step_failed`
with the same body only if your pipeline also routes `FailStepError` outcomes
through a separate failure hook; both hooks share the
`ctx.order_state.action` + `ctx.order_state.handled` contract shown above.

The hook above applies any declared action generically. When you need
due-date-specific handling (a notification, a metric, a distinct status note),
identify it by the exception type — `isinstance(error, DueDateReachedError)` —
since several steps may raise `StopStepError` in the same pipeline.
