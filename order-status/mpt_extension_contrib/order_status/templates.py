"""Resolve MPT order templates by name with fallback to the product default."""

import logging
from enum import StrEnum

from mpt_extension_sdk.models import Template
from mpt_extension_sdk.services.mpt_api_service import MPTAPIService

logger = logging.getLogger(__name__)


class OrderStatus(StrEnum):
    """MPT order statuses supported by the order-status pipeline steps.

    Extend this enum as more statuses need template resolution.
    """

    PROCESSING = "Processing"
    COMPLETED = "Completed"


async def resolve_template(
    api_service: MPTAPIService,
    *,
    product_id: str,
    status: OrderStatus,
    template_name: str | None = None,
) -> Template | None:
    """Return the named order template for a status, or the product default.

    The SDK template service returns the named template when it exists and falls
    back to the status default otherwise. When a name was requested but not
    matched, an info log records that the default is used instead, mirroring the
    per-extension behaviour this library replaces.

    Args:
        api_service: The MPT API service from the pipeline context.
        product_id: Identifier of the product owning the templates.
        status: Order status the template applies to.
        template_name: Preferred template name; ``None`` selects the default.

    Returns:
        The resolved template, or ``None`` when the product has no template for
        the status.
    """
    template = await api_service.templates.get_template(
        product_id, status.value, name=template_name
    )
    if template_name and (template is None or template.name != template_name):
        logger.info(
            "Template %r not found for status %s; using default %r instead.",
            template_name,
            status.value,
            None if template is None else template.name,
        )
    return template
