"""Build MPT parameter bags from a flat consumer catalog.

Parameter values are product-specific, so the catalog lives in the consumer.
These helpers only turn a flat ``{external_id: value}`` mapping into the SDK
``ParameterBag`` shape.
"""

from __future__ import annotations

from typing import Any

from mpt_extension_sdk.models import ParameterBag
from mpt_extension_sdk.models.parameter import ParameterValue


def parameter_bag(
    *,
    ordering: dict[str, Any] | None = None,
    fulfillment: dict[str, Any] | None = None,
) -> ParameterBag:
    """Build a ``ParameterBag`` from flat ordering and fulfillment catalogs.

    Each catalog maps a parameter ``externalId`` to its value. Omitted phases
    produce an empty list, which matches the SDK default.
    """
    return ParameterBag(
        ordering=_parameter_values(ordering),
        fulfillment=_parameter_values(fulfillment),
    )


def _parameter_values(catalog: dict[str, Any] | None) -> list[ParameterValue]:
    """Render a phase catalog into a list of ``ParameterValue`` objects."""
    return [
        ParameterValue(external_id=external_id, value=raw_value)
        for external_id, raw_value in (catalog or {}).items()
    ]
