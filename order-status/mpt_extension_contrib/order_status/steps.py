"""Pipeline steps that switch MPT order status and template with default fallback."""

import logging
from typing import override

from mpt_extension_contrib.order_status.templates import OrderStatus, resolve_template
from mpt_extension_sdk.errors.step import SkipStepError, StopStepError
from mpt_extension_sdk.pipeline import BaseStep, OrderContext, refresh_order

logger = logging.getLogger(__name__)


class CompleteOrder(BaseStep):
    """Switch an order to ``Completed`` using a template, with default fallback.

    The completion template is resolved by name from the order's product and
    falls back to the status default when the name is not found. The current
    order parameters are persisted with the completion. The step is skipped when
    the order is already completed, so it is safe to reprocess.
    """

    def __init__(self, *, template_name: str | None = None) -> None:
        """Store the preferred completion template name.

        Args:
            template_name: Template name to use; ``None`` uses the default.
        """
        self._template_name = template_name

    @override
    async def pre(self, context: OrderContext) -> None:
        """Skip the step when the order is already completed.

        Args:
            context: The order pipeline context.

        Raises:
            SkipStepError: When the order status is already ``Completed``.
        """
        if context.order.status == OrderStatus.COMPLETED:
            raise SkipStepError("order is already completed")

    @override
    @refresh_order
    async def process(self, context: OrderContext) -> None:
        """Complete the order with the resolved template, then refresh it.

        Args:
            context: The order pipeline context.

        Raises:
            StopStepError: When the product has no completion template at all.
        """
        product_id = context.order.product_id
        template = await resolve_template(
            context.mpt_api_service,
            product_id=product_id,
            status=OrderStatus.COMPLETED,
            template_name=self._template_name,
        )
        if template is None:
            raise StopStepError(f"no completion template found for product {product_id}")
        await context.mpt_api_service.orders.complete(
            context.order_id,
            template,
            {"parameters": context.order.parameters.to_dict()},
        )
        logger.info("%s: order has been completed", context.order_id)


class StartOrderProcessing(BaseStep):
    """Set the ``Processing`` template once, with default fallback.

    The processing template is resolved by name from the order's product and
    falls back to the status default when the name is not found. It is applied
    only when it differs from the template already on the order, so reprocessing
    leaves the order untouched. When the product has no matching template the
    step logs a warning and continues.
    """

    def __init__(self, *, template_name: str | None = None) -> None:
        """Store the preferred processing template name.

        Args:
            template_name: Template name to use; ``None`` uses the default.
        """
        self._template_name = template_name

    @override
    async def process(self, context: OrderContext) -> None:
        """Apply the processing template when it is not already set.

        Args:
            context: The order pipeline context.
        """
        template = await resolve_template(
            context.mpt_api_service,
            product_id=context.order.product_id,
            status=OrderStatus.PROCESSING,
            template_name=self._template_name,
        )
        if template is None:
            logger.warning(
                "%s: no processing template found for product %s; continuing.",
                context.order_id,
                context.order.product_id,
            )
            return
        current_template_id = None if context.order.template is None else context.order.template.id
        if template.id == current_template_id:
            logger.info("%s: processing template already set, continuing", context.order_id)
            return
        await context.mpt_api_service.templates.set_order_template(context.order_id, template)
        await context.refresh_order()
        logger.info("%s: processing template set to %s", context.order_id, template.id)
