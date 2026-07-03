# Usage

This guide covers installing the library, adding the steps to a pipeline, and
how the steps resolve templates.

## 1. Install

```bash
pip install mpt-extension-contrib-order-status
```

Requires the Extension SDK (`mpt-extension-sdk >= 6.3, < 7`), pulled in as a
dependency.

## 2. Add the steps to a pipeline

Pass the template name each step should prefer. Omit `template_name` to use the
product's default template for the status.

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

- `StartOrderProcessing(template_name=...)` — sets the `Processing` template on
  the order. It applies the template only when it differs from the one already
  set, so the step is a no-op when reprocessing. When the product has no
  matching template it logs a warning and continues.
- `CompleteOrder(template_name=...)` — completes the order with the `Completed`
  template, then refreshes the context order. It is skipped when the order is
  already `Completed`, and it raises `StopStepError` when the product has no
  completion template at all.

## 3. Template resolution and fallback

Both steps resolve their template with `resolve_template`, which calls the SDK
template service and falls back to the product default when the requested name
is not configured:

```python
from mpt_extension_contrib.order_status import OrderStatus, resolve_template

template = await resolve_template(
    context.mpt_api_service,
    product_id=context.order.product_id,
    status=OrderStatus.COMPLETED,
    template_name="Purchase completed",
)
```

When the requested name is not found, the default template for the status is
used and an info log records the fallback, so a misconfigured template name is
visible in the logs without failing the order.

## 4. Overriding template selection

Each step calls its own `async resolve_template(self, context)` method, which
delegates to the module-level helper by default. Subclass a step and override
this method when the template to use depends on order content instead of a
fixed name:

```python
from mpt_extension_contrib.order_status import CompleteOrder, OrderStatus, resolve_template


class CompletePurchaseOrder(CompleteOrder):
    async def resolve_template(self, context):
        if context.order.parameters.get_fulfillment_value("isNewUser"):
            return await resolve_template(
                context.mpt_api_service,
                product_id=context.order.product_id,
                status=OrderStatus.COMPLETED,
                template_name="Purchase completed (existing account)",
            )
        return await super().resolve_template(context)
```

Use `CompletePurchaseOrder(template_name="Purchase completed")` in the pipeline
as usual; the constructor argument is still available to `super().resolve_template()`.
