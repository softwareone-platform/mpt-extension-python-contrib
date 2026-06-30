# mpt-extension-contrib-order-status

Shared **order-status** pipeline steps for SoftwareONE MPT extensions built on
the Extension SDK. The steps switch an order to its next status using a named
order template and fall back to the product default when that template is not
configured, so status changes stay consistent across extensions.

It replaces the per-extension complete-order and start-processing logic
previously re-implemented in the Adobe, AWS, and FinOps extensions.

See [AGENTS.md](AGENTS.md) for the module documentation map.

## Install

```bash
pip install mpt-extension-contrib-order-status
```

Requires the Extension SDK (`mpt-extension-sdk >= 6.3, < 7`), which is pulled in
as a dependency.

## Public API

`mpt_extension_contrib.order_status` exposes two pipeline steps, one helper, and
one enum:

| Object | Purpose |
| --- | --- |
| `CompleteOrder(template_name=...)` | Switch the order to `Completed` with a named template, falling back to the default. |
| `StartOrderProcessing(template_name=...)` | Set the `Processing` template on the first run, falling back to the default. |
| `resolve_template(api_service, *, product_id, status, template_name=None)` | Resolve a status template by name with default fallback (the primitive both steps use). |
| `OrderStatus` | `StrEnum` of the order statuses the library resolves templates for (`PROCESSING`, `COMPLETED`). |

`template_name` is optional on both steps; omit it to use the product's default
template for the status.

## Usage

Add the steps to an order pipeline:

```python
from mpt_extension_sdk.pipeline import BasePipeline, BaseStep

from mpt_extension_contrib.order_status import CompleteOrder, StartOrderProcessing


class PurchasePipeline(BasePipeline):
    @property
    def steps(self) -> list[BaseStep]:
        return [
            StartOrderProcessing(template_name="Purchase processing"),
            # ... order processing steps ...
            CompleteOrder(template_name="Purchase completed"),
        ]
```

- `StartOrderProcessing(template_name=...)` — resolves the `Processing` template
  and applies it only when it differs from the one already on the order, so
  reprocessing is a no-op. When the product has no matching template it logs a
  warning and continues.
- `CompleteOrder(template_name=...)` — resolves the `Completed` template,
  completes the order with the current parameters, and refreshes the context
  order. It is skipped when the order is already completed and stops the
  pipeline when the product has no completion template at all.

Both steps fall back to the product default template when the requested name is
not found, logging that the default was used. See [Usage](docs/usage.md) for the
full setup.

## Documentation

- [Usage](docs/usage.md) — install, add the steps, and template resolution
- [Architecture](docs/architecture.md)
- [Contributing](docs/contributing.md)
- [Testing](docs/testing.md)
- [Releases](docs/releases.md)
