# Architecture

`mpt-extension-contrib-reports` provides reusable building blocks for
generating tabular vendor reports and publishing them to Confluence.

## Public API boundary

The package root `mpt_extension_contrib.reports` exports only the
integration surface:

```python
from mpt_extension_contrib.reports import (
    publish_xlsx_to_confluence,
    publish_xlsx_to_confluence_async,
    PendingOrdersReportSettings,
    ConfluenceClient,
    ExcelReportBuilder,
    ReportCreator,
    AsyncReportCreator,
    Report,
    QueryableService,
    AsyncQueryableService,
    PENDING_ORDER_STATUSES,
    EXCEL_MIME_TYPE,
    ReportRow,
    ReportRows,
    RowMapper,
    SheetDefinition,
)
```

- `publish_xlsx_to_confluence` is the turnkey job for the original AWS use
  case: it fetches the pending orders, builds a workbook, and attaches it to a
  Confluence page under a date-stamped filename with a total-count comment. It
  is a thin composition of the building blocks below. It reads the Confluence
  config and page id from an injected `settings` object; its `row_mapper` and
  `headers` are optional — omitted, the columns are inferred from the order
  fields.
- `PendingOrdersReportSettings` is the `Protocol` for that `settings` object:
  `confluence_base_url`, `confluence_user`, `confluence_token`, and
  `pending_orders_information_report_page_id`. An extension's `ExtensionSettings` satisfies
  it structurally.
- `ReportCreator` fetches any queryable Marketplace collection (orders,
  subscriptions, agreements, ...) matching an optional RQL query and builds a
  `Report`. With a `RowMapper` the caller owns the columns; without one, each
  payload is flattened (nested dicts become dotted-path columns) and headers are
  inferred.
- `Report` is the `NamedTuple` returned by `ReportCreator.create()`: the data
  `rows` and the `headers` (inferred when no `RowMapper`; empty when one is set,
  so the caller supplies headers).
- `publish_xlsx_to_confluence_async` / `AsyncReportCreator` (with the
  `AsyncQueryableService` protocol) are the async counterparts for an
  `AsyncMPTClient`: identical behaviour, fetched with `async for`. They live in
  `report_async.py` and reuse the same `build_report` projection; the blocking
  Confluence upload runs in a worker thread (`asyncio.to_thread`).
- `ExcelReportBuilder` turns headers and rows into `.xlsx` bytes
  (single sheet via `build_sheet`, several via `build_multi_sheet`).
- `ConfluenceClient` attaches file bytes to a Confluence page.
- `QueryableService` is the `Protocol` describing the collection
  `ReportCreator` accepts (`filter`/`select`/`iterate`); any `mpt_api_client`
  collection such as `client.commerce.orders` satisfies it.
- `PENDING_ORDER_STATUSES` is the tuple of order statuses
  (`Querying`, `Processing`) the pending-orders job filters on.
- `EXCEL_MIME_TYPE` is the MIME type for `.xlsx` workbooks, passed as the
  required `content_type` argument when attaching them.
- `ReportRow`, `ReportRows`, `RowMapper`, `SheetDefinition` are the type
  aliases used across the public surface.

## Design

- **No product-specific columns are baked in.** The column layout lives in the
  `RowMapper` callable the caller passes to `ReportCreator`; the filter is an
  `mpt_api_client` `RQLQuery`. The package fetches and maps; it does not know
  about any vendor's resource parameters.
- **Configuration is injected explicitly.** `ConfluenceClient` takes
  `base_url`, `user`, and `token` directly, so it has no dependency on any
  extension settings object or framework.
- **Single responsibility per component.** Fetching/mapping resources, building
  the workbook, and attaching it to Confluence are independent pieces a caller
  composes for a specific report.

## Composing a report

The pending-orders job packages the original AWS use case end to end — the
caller supplies the API client, the extension `settings` (Confluence config +
page id), and the column layout:

```python
from mpt_extension_contrib.reports import publish_xlsx_to_confluence

HEADERS = ["ID", "Order Type", "Status", "Product"]


def to_row(order):
    return [
        order.get("id", ""),
        order.get("type", ""),
        order.get("status", ""),
        order.get("product", {}).get("name", ""),
    ]


publish_xlsx_to_confluence(
    mpt_client,
    settings,  # satisfies PendingOrdersReportSettings
    row_mapper=to_row,
    headers=HEADERS,
)
```

Internally that is the following composition, which you can also assemble
yourself for any other report (different collection, filter, or output):

```python
from mpt_api_client.rql import RQLQuery
from mpt_extension_contrib.reports import (
    EXCEL_MIME_TYPE,
    PENDING_ORDER_STATUSES,
    ReportCreator,
)

creator = ReportCreator(
    mpt_client.commerce.orders,
    to_row,
    query=RQLQuery(status__in=list(PENDING_ORDER_STATUSES)),
    select=["audit", "parameters"],
)
report = creator.create()  # Report(headers, rows)

workbook = ExcelReportBuilder(HEADERS, sheet_name="Pending Orders").build_sheet(report.rows)

ConfluenceClient(base_url, user, token).attach_content(
    page_id,
    "orders-2026-06-26.xlsx",
    workbook,
    content_type=EXCEL_MIME_TYPE,
    comment=f"Total orders {len(report.rows)}",
)
```
