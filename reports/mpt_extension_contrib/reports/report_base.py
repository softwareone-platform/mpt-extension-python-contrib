"""Shared configuration and narrowing for the sync and async report creators."""

import logging
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Protocol, Self

from mpt_api_client.rql import RQLQuery

logger = logging.getLogger(__name__)

type ReportRow = list[str]
type ReportRows = list[ReportRow]
type RowMapper = Callable[[Mapping[str, Any]], ReportRow]


class NarrowableService(Protocol):
    """A Marketplace collection that can be filtered and column-narrowed."""

    def filter(self, rql: RQLQuery) -> Self:
        """Return a copy of the collection narrowed by an RQL filter."""

    def select(self, *fields: str) -> Self:
        """Return a copy of the collection that includes the given attributes."""


class BaseReportCreator[ServiceT: NarrowableService]:
    """Holds the query configuration shared by the sync and async creators.

    Subclasses add a ``create()`` that iterates the narrowed collection; the
    fetch is the only thing that differs between the sync and async variants.
    """

    def __init__(
        self,
        service: ServiceT,
        row_mapper: RowMapper | None = None,
        *,
        query: RQLQuery | None = None,
        select: Sequence[str] | None = None,
        batch_size: int = 100,
    ) -> None:
        """Initialize the creator.

        Args:
            service: A queryable Marketplace collection, e.g. ``client.commerce.orders``.
            row_mapper: Maps a single resource payload to a report row. When ``None``,
                each payload is flattened (nested dicts become dotted columns).
            query: Optional RQL filter applied to the collection.
            select: Optional resource attributes to include in each payload.
            batch_size: Page size used while iterating the collection.
        """
        self._service = service
        self._row_mapper = row_mapper
        self._query = query
        self._select = select
        self._batch_size = batch_size

    def _narrowed_service(self) -> ServiceT:
        """Apply the query and column selection, returning the narrowed collection."""
        logger.debug(
            "Fetching resources (query=%s, select=%s, batch_size=%d)",
            self._query,
            self._select,
            self._batch_size,
        )
        service = self._service
        if self._query is not None:
            service = service.filter(self._query)
        if self._select:
            service = service.select(*self._select)
        return service
