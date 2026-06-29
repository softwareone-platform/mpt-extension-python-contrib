"""Async counterpart of :mod:`report` for an ``AsyncMPTClient`` collection."""

from collections.abc import AsyncIterator
from typing import Any, Protocol

from mpt_extension_contrib.reports.report import Report, build_report
from mpt_extension_contrib.reports.report_base import BaseReportCreator, NarrowableService


class AsyncQueryableService(NarrowableService, Protocol):
    """An async Marketplace collection that can be filtered, narrowed, and iterated."""

    def iterate(self, batch_size: int = 100) -> AsyncIterator[Any]:
        """Asynchronously yield each resource, paginating by ``batch_size``."""


class AsyncReportCreator(BaseReportCreator[AsyncQueryableService]):
    """Async counterpart of ``ReportCreator`` for an ``AsyncMPTClient`` collection.

    Behaves exactly like the synchronous ``ReportCreator`` — same ``row_mapper``
    and header-inference rules — but fetches the collection with ``async for``.
    """

    async def create(self) -> Report:
        """Fetch the matching resources and build the report.

        Returns:
            The report ``headers`` (empty when a ``row_mapper`` is set) and one
            row per matching resource, in collection order.
        """
        service = self._narrowed_service()
        payloads = [
            resource.to_dict() async for resource in service.iterate(batch_size=self._batch_size)
        ]
        return build_report(payloads, self._row_mapper)
