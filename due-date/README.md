# mpt-extension-contrib-due-date

Shared **order processing due-date** helpers for SoftwareONE MPT extensions built
on the Extension SDK. The library sets a maximum date by which an order must be
processed and fails the order once that date passes, so orders never hang in
processing forever.

It replaces the per-extension due-date logic previously re-implemented in the
Adobe and FinOps extensions.

See [AGENTS.md](AGENTS.md) for the module documentation map.

## Install

```bash
pip install mpt-extension-contrib-due-date
```

Requires the Extension SDK (`mpt-extension-sdk >= 6.3, < 7`), which is pulled in as a
dependency.

## Public API

`mpt_extension_contrib.due_date` exposes three pipeline steps and one settings
contract:

| Object | Purpose |
| --- | --- |
| `SetDueDate(days=N)` | Set `today + N` days as the due date and persist it (once). |
| `EnforceDueDate()` | Fail the order when its due date has been reached. |
| `ResetDueDate()` | Clear the due date, e.g. before completing the order. |
| `DueDateSettings` | `Protocol` describing the settings the steps read. |

## Usage

Expose the due-date parameter external id in the extension settings:

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

Add the steps to an order pipeline:

```python
from mpt_extension_sdk.pipeline import BasePipeline, BaseStep

from mpt_extension_contrib.due_date import EnforceDueDate, ResetDueDate, SetDueDate


class PurchasePipeline(BasePipeline):
    @property
    def steps(self) -> list[BaseStep]:
        return [
            SetDueDate(days=14),  # assign the deadline on first run
            EnforceDueDate(),  # fail the order once the deadline passes
            # ... order processing steps ...
            ResetDueDate(),  # clear the deadline before completing
        ]
```

The steps read the parameter external id from
`context.ext_settings.due_date_parameter` and the deadline length from
`SetDueDate(days=...)`.

`EnforceDueDate` does not fail the order itself: it records the intent and raises
`DueDateReachedError` (a `StopStepError`), which the extension's pipeline applies
in an `on_step_stopped` / `on_step_failed` hook. See [Usage](docs/usage.md) for
the full setup, including the failure hook.

## Documentation

- [Usage](docs/usage.md) — install, configure, add the steps, and fail on the deadline
- [Architecture](docs/architecture.md)
- [Contributing](docs/contributing.md)
- [Testing](docs/testing.md)
- [Releases](docs/releases.md)
