# mpt-extension-contrib-phase-step

Shared **provisioning-phase gating** for SoftwareONE MPT extensions built on the
Extension SDK. A step declares the single provisioning phase it runs for; when
the order's phase parameter holds a different value the step is skipped and the
pipeline records the skip, instead of the step deciding to no-op inside its own
body.

It replaces ad-hoc phase checks inside individual extension steps with one
reusable gating mechanism shared across pipelines.

See [AGENTS.md](AGENTS.md) for the module documentation map.

## Install

```bash
pip install mpt-extension-contrib-phase-step
```

Requires the Extension SDK (`mpt-extension-sdk >= 6.3, < 7`), which is pulled in as a
dependency.

## Public API

`mpt_extension_contrib.phase_step` exposes a base step, two functions, and one
settings contract:

| Object | Purpose |
| --- | --- |
| `PhaseGatedStep(expected_phases)` | Base step that runs only when the order phase is one of `expected_phases` (a phase or a list of phases); subclass and implement `process()`. |
| `require_phase(context, expected_phases)` | Guard for a hand-written `pre()`: skip the step unless the phase is one of `expected_phases`. |
| `advance_phase(context, phase)` | Persist a new phase on the order (and refresh the context) to move the flow forward; call it from `process()`. |
| `PhaseStepSettings` | `Protocol` describing the settings the API reads. |

## Design in one line

The SDK already skips a step when its `pre()` raises `SkipStepError` (the
pipeline logs the skip and continues). This library adds only the missing
convention — read the phase parameter, compare, raise — as a function and a
thin base step, and keeps phase values and the parameter id out of the library.
No decorators or wrappers: gating is expressed by subclassing and, when needed,
an explicit `await super().pre(context)`.

## Usage

Expose the phase parameter external id in the extension settings:

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

Seed the phase before the first gated step: `PhaseGatedStep.pre()` runs before
`process()`, so a first step with an unset phase would skip before it could
initialize it. Set an initial value via a product default or an ungated
initializer step.

Gate a step by subclassing `PhaseGatedStep` and binding the phase when the
pipeline is composed:

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

See [Usage](docs/usage.md) for a step that adds its own `pre()` guard and for
advancing the phase.

## Documentation

- [Usage](docs/usage.md) — install, configure, gate steps, advance the phase
- [Architecture](docs/architecture.md)
- [Contributing](docs/contributing.md)
- [Testing](docs/testing.md)
- [Releases](docs/releases.md)
