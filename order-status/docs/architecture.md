# Architecture

`mpt-extension-contrib-order-status` provides reusable order-status pipeline
steps for extensions built on the Extension SDK.

## Public API boundary

The public API is the `mpt_extension_contrib.order_status` package:

```python
from mpt_extension_contrib.order_status import (
    CompleteOrder,
    OrderStatus,
    StartOrderProcessing,
    resolve_template,
)
```

- `steps.py` holds the `BaseStep` subclasses `CompleteOrder` and
  `StartOrderProcessing`.
- `templates.py` holds `resolve_template`, the status-template resolution
  primitive, and the `OrderStatus` enum (`PROCESSING`, `COMPLETED`). Extend the
  enum as more statuses need template resolution.

Both submodules are re-exported from the package `__init__`; import from the
package root rather than the submodules.

## Design

- The steps operate only on the SDK `OrderContext` and its `mpt_api_service`.
  They read `context.order` (product, status, template, parameters) and call the
  SDK order and template services; they carry no product-specific logic.
- Template resolution delegates to the SDK `TemplateService.get_template`, which
  returns the named template or the status default. The module-level
  `resolve_template` helper adds the fallback log so operators can see when a
  configured name was missing.
- Each step exposes an overridable `async resolve_template(self, context)`
  method that calls the module-level helper by default. Subclass a step and
  override this method to select a template with custom logic (e.g. by order
  content) instead of a fixed name; see [Usage](usage.md).
- `CompleteOrder` completes the order through `orders.complete`, passing only
  the resolved template. It does not resend `context.order.parameters`: the
  step does not mutate them, and the SDK `OrderService.complete` treats
  attributes as optional. There is no `Completed` order-status action type in
  the SDK, so completion is a direct service call rather than a declared
  `OrderStatusAction`.
- `StartOrderProcessing` applies the template through
  `templates.set_order_template` only when it differs from the current one,
  keeping reprocessing idempotent.
