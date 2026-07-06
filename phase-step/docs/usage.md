# Usage

This guide covers installing the library, configuring the phase parameter,
gating steps on the provisioning phase, and advancing the phase.

## 1. Install

```bash
pip install mpt-extension-contrib-phase-step
```

Requires the Extension SDK (`mpt-extension-sdk >= 6.3, < 7`), pulled in as a
dependency.

## 2. Provide the phase parameter

The library does **not** create the phase parameter — it is a prerequisite the
extension owns. Define a single-choice fulfillment parameter on the product
whose value is the current provisioning phase (for example `phase`), and set an
initial value in the first pipeline step so gated steps have something to match.

The phase is the extension's own fulfillment sub-state (e.g. `createSubscription`,
`checkOnboardStatus`), tracked in this parameter — it is **not** the MPT order
status (`Processing`, `Querying`, `Completed`, on `context.order.status`). Gating
is about *where in your fulfillment flow* the order is, not its platform status.

The helpers read the parameter's external id from
`context.ext_settings.phase_parameter`. Inherit `PhaseStepSettings` on the
extension settings so the contract is type-checked:

```python
from dataclasses import dataclass
from typing import Self, override

from mpt_extension_sdk.settings.extension import BaseExtensionSettings

from mpt_extension_contrib.phase_step import PhaseStepSettings


@dataclass(frozen=True)
class ExtensionSettings(BaseExtensionSettings, PhaseStepSettings):
    phase_parameter: str = "phase"

    @override
    @classmethod
    def load(cls) -> Self:
        return cls()
```

## 3. Gate your own step

Subclass `PhaseGatedStep` and implement `process()`. The expected phase is
bound per instance when the pipeline is composed, so the same class can be
reused later with a different phase.

```python
from typing import override

from mpt_extension_sdk.pipeline import BasePipeline, BaseStep, OrderContext

from mpt_extension_contrib.phase_step import PhaseGatedStep


class CreateSubscription(PhaseGatedStep):
    @override
    async def process(self, context: OrderContext) -> None:
        # runs only while the phase parameter equals the bound value
        ...


class PurchasePipeline(BasePipeline):
    @property
    def steps(self) -> list[BaseStep]:
        return [
            CreateSubscription("createSubscription"),
            # ... more phase-gated steps ...
        ]
```

To run a step for any of several phases, pass a list instead of a single
value — `CreateSubscription(["createSubscription", "createExistingSubscription"])`;
the step runs while the phase equals any of them.

When the phase does not match, `pre()` raises `SkipStepError`; the SDK pipeline
logs `Step CreateSubscription skipped - reason: …` and continues with the next
step. `process()` never runs and stays focused on the actual work.

### A step that needs its own `pre()`

Override `pre()` and call `super().pre(context)` first, so the phase check runs
before the step's own guard and the order is explicit in the method body:

```python
from typing import override

from mpt_extension_sdk.errors.step import SkipStepError
from mpt_extension_sdk.pipeline import OrderContext

from mpt_extension_contrib.phase_step import PhaseGatedStep


class CreateSubscription(PhaseGatedStep):
    @override
    async def pre(self, context: OrderContext) -> None:
        await super().pre(context)  # skip unless the phase matches
        # `_subscription_already_exists` is your extension's own check
        if _subscription_already_exists(context.order):
            raise SkipStepError("subscription already created")
```

## 4. Advance the phase

Gating and advancing are separate responsibilities: gating is a read the base
step does in `pre()`, while advancing the phase is a write the step makes
explicitly in `process()`, at the point it decides to move forward. Use
`advance_phase`:

```python
from typing import override

from mpt_extension_sdk.pipeline import OrderContext

from mpt_extension_contrib.phase_step import PhaseGatedStep, advance_phase


class CreateSubscription(PhaseGatedStep):
    @override
    async def process(self, context: OrderContext) -> None:
        # ... do the work ...
        await advance_phase(context, "completed")
```

`advance_phase(context, phase)` writes the phase fulfillment parameter (named
by the `phase_parameter` setting), persists it through `mpt_api_service`, and
then refreshes `context.order`.

### It refreshes `context.order` after the write

The refresh keeps the persisted and in-memory phase consistent: a later gated
step in the same pipeline run reads the new phase from `context.order` and gates
correctly, rather than seeing the stale value and being skipped. This is the
read-after-write case the SDK pipeline-steps guideline refreshes for — gated
steps read from `context.order`, so a step that advances the phase must leave the
snapshot updated for the steps that follow it in the same run.

The refresh is one extra fetch. A caller that must avoid it — advancing as the
very last step, or batching the phase into a larger order update — can drop to
the lower level and skip the helper:

```python
external_id = context.ext_settings.phase_parameter
parameters = context.order.parameters.with_fulfillment_value(external_id, "completed")
await context.mpt_api_service.orders.update(
    context.order_id, {"parameters": parameters.to_dict()}
)  # persists without refreshing; only when nothing downstream reads it
```

An "already done, move on" case is expressed the same way: advance the phase in
`pre()` and raise `SkipStepError` — the SDK handles the skip, so no special error
type is needed.
