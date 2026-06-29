"""Build report rows from a Marketplace resource collection."""

import logging
from collections.abc import Iterator, Mapping
from typing import Any, NamedTuple, Protocol

from mpt_extension_contrib.reports.report_base import (
    BaseReportCreator,
    NarrowableService,
    ReportRows,
    RowMapper,
)

logger = logging.getLogger(__name__)


class Report(NamedTuple):
    """A built report: the column headers and the data rows under them."""

    headers: list[str]
    rows: ReportRows


def _flatten(payload: Mapping[str, Any], prefix: str = "") -> dict[str, str]:
    """Flatten nested dicts into dotted-path columns; stringify the leaves.

    Nested mappings become ``parent.child`` columns; ``None`` becomes ``""`` and
    every other leaf (including lists) is stringified.
    """
    flat: dict[str, str] = {}
    for key, field in payload.items():
        column = f"{prefix}{key}"
        if isinstance(field, Mapping):
            flat.update(_flatten(field, f"{column}."))
        else:
            flat[column] = "" if field is None else str(field)
    return flat


def _infer_report(payloads: list[Mapping[str, Any]]) -> "Report":
    """Build a report by flattening each payload into a row.

    Every payload is assumed to share the same shape, so the first row's columns
    define the headers for all of them.
    """
    flattened = [_flatten(payload) for payload in payloads]
    headers = list(flattened[0]) if flattened else []
    rows = [list(cells.values()) for cells in flattened]
    return Report(headers=headers, rows=rows)


def build_report(payloads: list[Mapping[str, Any]], row_mapper: RowMapper | None) -> "Report":
    """Map payloads to a report: caller's ``row_mapper``, or inferred when ``None``.

    Shared by the sync and async report creators.
    """
    if row_mapper is None:
        report = _infer_report(payloads)
    else:
        report = Report(headers=[], rows=[row_mapper(payload) for payload in payloads])
    logger.info("Built report with %d rows", len(report.rows))
    return report


class QueryableService(NarrowableService, Protocol):
    """A Marketplace collection that can be filtered, narrowed, and iterated."""

    def iterate(self, batch_size: int = 100) -> Iterator[Any]:
        """Yield each resource in the collection, paginating by ``batch_size``."""


class ReportCreator(BaseReportCreator[QueryableService]):
    """Fetch resources matching a query and build a report from them.

    The filter is an ``mpt_api_client`` ``RQLQuery`` and the collection is any
    queryable Marketplace collection (orders, subscriptions, agreements, ...);
    no resource-specific fields are baked in.

    When a ``row_mapper`` is given it owns the column layout. When it is omitted,
    each resource payload is flattened (nested dicts become dotted-path columns)
    and the headers are inferred from the resulting fields.

    Warning:
        Inference assumes every resource has the same shape: headers come from
        the first payload while each row is built positionally from its own
        values. If the payloads differ in shape, a row's values can misalign
        with the headers and the report will silently mislabel columns. Pass an
        explicit ``row_mapper`` and ``headers`` when the payloads may differ.
    """

    def create(self) -> Report:
        """Fetch the matching resources and build the report.

        With a ``row_mapper`` the caller owns the columns, so ``headers`` is left
        empty for the caller to supply. Without one, payloads are flattened and
        ``headers`` are the inferred dotted-path field names.

        Returns:
            The report ``headers`` (empty when a ``row_mapper`` is set) and one
            row per matching resource, in collection order.
        """
        service = self._narrowed_service()
        payloads = [resource.to_dict() for resource in service.iterate(batch_size=self._batch_size)]
        return build_report(payloads, self._row_mapper)
