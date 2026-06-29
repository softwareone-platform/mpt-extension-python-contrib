"""Daily pending-orders report: fetch pending orders, build, and publish them."""

import asyncio
import datetime as dt
import logging
from collections.abc import Sequence
from typing import Protocol

from mpt_api_client import AsyncMPTClient, MPTClient
from mpt_api_client.rql import RQLQuery
from mpt_extension_contrib.reports.confluence import ConfluenceClient
from mpt_extension_contrib.reports.excel import EXCEL_MIME_TYPE, ExcelReportBuilder
from mpt_extension_contrib.reports.report import Report, ReportCreator
from mpt_extension_contrib.reports.report_async import AsyncReportCreator
from mpt_extension_contrib.reports.report_base import RowMapper

logger = logging.getLogger(__name__)

PENDING_ORDER_STATUSES = ("Querying", "Processing")
_PENDING_ORDER_SELECT = ("audit", "parameters")
_SHEET_NAME = "Pending Orders"


class PendingOrdersReportSettings(Protocol):
    """Extension settings the pending-orders report reads.

    An extension's ``ExtensionSettings`` satisfies this structurally by exposing
    these fields; it may also inherit this protocol to have the contract checked.
    """

    confluence_base_url: str
    confluence_user: str
    confluence_token: str
    pending_orders_information_report_page_id: str


def _require_layout_pair(row_mapper: RowMapper | None, headers: Sequence[str] | None) -> None:
    """Reject a half-specified layout: ``row_mapper`` and ``headers`` go together."""
    if (row_mapper is None) != (headers is None):
        raise ValueError("provide both row_mapper and headers, or neither")


def _build_attachment(
    report: Report,
    settings: PendingOrdersReportSettings,
    headers: Sequence[str] | None,
) -> tuple[str, str, bytes]:
    """Build the workbook from ``report`` and return the page id, filename, and bytes."""
    sheet_headers = report.headers if headers is None else list(headers)
    workbook = ExcelReportBuilder(sheet_headers, sheet_name=_SHEET_NAME).build_sheet(report.rows)
    today = dt.datetime.now(tz=dt.UTC).strftime("%d-%m-%Y")
    page_id = settings.pending_orders_information_report_page_id
    logger.info(
        "Publishing pending-orders report (%d orders) to Confluence page %s",
        len(report.rows),
        page_id,
    )
    return page_id, f"orders-{today}.xlsx", workbook


def _confluence(settings: PendingOrdersReportSettings) -> ConfluenceClient:
    """Build the Confluence client from the extension settings."""
    return ConfluenceClient(
        base_url=settings.confluence_base_url,
        user=settings.confluence_user,
        token=settings.confluence_token,
    )


def publish_xlsx_to_confluence(
    client: MPTClient,
    settings: PendingOrdersReportSettings,
    *,
    row_mapper: RowMapper | None = None,
    headers: Sequence[str] | None = None,
    select: Sequence[str] = _PENDING_ORDER_SELECT,
) -> bool:
    """Generate the daily pending-orders report and attach it to a Confluence page.

    Fetches every order in a pending status (querying or processing) from the
    Marketplace orders collection, builds an ``.xlsx`` workbook, and attaches it
    to the Confluence page from ``settings`` under a date-stamped filename with a
    comment recording the total order count. The sheet name is fixed.

    The Confluence base URL, credentials, and target page id all come from
    ``settings``, so callers configure them once on their extension settings
    rather than passing them here.

    ``row_mapper`` and ``headers`` are a pair: pass both to control the exact
    column layout, or neither to get an inferred report (each order payload is
    flattened, nested dicts becoming dotted-path columns, and the headers are
    the inferred field names). ``select`` controls which order attributes are
    fetched, so narrow it to match ``row_mapper`` (or to limit what an inferred
    report exposes).

    Args:
        client: Marketplace API client; its ``commerce.orders`` collection is queried.
        settings: Extension settings providing the Confluence config and page id.
        row_mapper: Optional mapper from an order payload to a report row.
        headers: Optional column headers, in column order.
        select: Order attributes to include in each payload.

    Returns:
        ``True`` if the report was attached successfully, ``False`` otherwise.

    Raises:
        ValueError: If only one of ``row_mapper`` and ``headers`` is provided.
    """
    _require_layout_pair(row_mapper, headers)
    report = ReportCreator(
        client.commerce.orders,
        row_mapper,
        query=RQLQuery(status__in=list(PENDING_ORDER_STATUSES)),
        select=select,
    ).create()
    page_id, filename, workbook = _build_attachment(report, settings, headers)
    return _confluence(settings).attach_content(
        page_id,
        filename,
        workbook,
        content_type=EXCEL_MIME_TYPE,
        comment=f"Total orders {len(report.rows)}",
    )


async def publish_xlsx_to_confluence_async(
    client: AsyncMPTClient,
    settings: PendingOrdersReportSettings,
    *,
    row_mapper: RowMapper | None = None,
    headers: Sequence[str] | None = None,
    select: Sequence[str] = _PENDING_ORDER_SELECT,
) -> bool:
    """Async counterpart of :func:`publish_xlsx_to_confluence` for an ``AsyncMPTClient``.

    Fetches the pending orders with ``async for``; the blocking Confluence upload
    runs in a worker thread so the event loop is not blocked. Behaviour is
    otherwise identical to the synchronous version, including the ``row_mapper``/
    ``headers`` pairing rule, the ``select`` control, and the settings-driven
    Confluence config.

    Args:
        client: Async Marketplace API client; its ``commerce.orders`` is queried.
        settings: Extension settings providing the Confluence config and page id.
        row_mapper: Optional mapper from an order payload to a report row.
        headers: Optional column headers, in column order.
        select: Order attributes to include in each payload.

    Returns:
        ``True`` if the report was attached successfully, ``False`` otherwise.

    Raises:
        ValueError: If only one of ``row_mapper`` and ``headers`` is provided.
    """
    _require_layout_pair(row_mapper, headers)
    report = await AsyncReportCreator(
        client.commerce.orders,
        row_mapper,
        query=RQLQuery(status__in=list(PENDING_ORDER_STATUSES)),
        select=select,
    ).create()
    page_id, filename, workbook = _build_attachment(report, settings, headers)
    return await asyncio.to_thread(
        _confluence(settings).attach_content,
        page_id,
        filename,
        workbook,
        content_type=EXCEL_MIME_TYPE,
        comment=f"Total orders {len(report.rows)}",
    )
