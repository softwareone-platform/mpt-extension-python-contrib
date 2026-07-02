# Usage

This guide covers installing the library, running the turnkey daily
pending-orders report, and composing the building blocks for other reports.

## 1. Install

```bash
pip install mpt-extension-contrib-reports
```

Compatible with the Extension SDK `>= 6.0.0`; it depends on `mpt-api-client`
(the Marketplace API client) plus `openpyxl`, `requests`, and
`atlassian-python-api`, pulled in as dependencies.

## 2. Publish the daily pending-orders report

`publish_xlsx_to_confluence` packages the original AWS use case end to end:
it queries the client's `commerce.orders` for pending orders, builds an `.xlsx`
workbook, and attaches it to a Confluence page under a date-stamped filename
(`orders-DD-MM-YYYY.xlsx`) with a `Total orders N` comment.

The Confluence config and target page come from your extension settings, which
must satisfy the `PendingOrdersReportSettings` protocol:

```python
class PendingOrdersReportSettings(Protocol):
    confluence_base_url: str
    confluence_user: str
    confluence_token: str
    pending_orders_information_report_page_id: str
```

Your `ExtensionSettings` satisfies it structurally by exposing those fields (or
inherit the protocol to have it checked). You pass the client, the settings, and
the column layout:

```python
from mpt_extension_contrib.reports import publish_xlsx_to_confluence

HEADERS = ["ID", "Order Type", "Status", "Product"]


def to_row(order: dict) -> list[str]:
    return [
        order.get("id", ""),
        order.get("type", ""),
        order.get("status", ""),
        order.get("product", {}).get("name", ""),
    ]


uploaded = publish_xlsx_to_confluence(
    client,  # an mpt_api_client.MPTClient
    settings,  # satisfies PendingOrdersReportSettings
    row_mapper=to_row,
    headers=HEADERS,
)
```

The job reads the Confluence base URL, credentials, and page id from `settings`,
and bakes in the pending-status filter (`PENDING_ORDER_STATUSES`), the workbook
build (sheet name included), the filename, and the comment.

`row_mapper` and `headers` are a pair — pass both (as above) for an explicit
layout, or omit both for a quick report whose columns are inferred from the
order fields, with nested objects flattened into dotted columns (e.g.
`client.id`, `audit.created.at`). Providing only one raises `ValueError`.
`select` (default `("audit", "parameters")`) controls which order attributes are
fetched — narrow it to match a custom `row_mapper`, or to limit what an inferred
report exposes:

```python
uploaded = publish_xlsx_to_confluence(client, settings)
```

### Async

For an `AsyncMPTClient`, use `publish_xlsx_to_confluence_async` — same arguments
and behaviour, fetched with `async for` (the blocking Confluence upload runs in a
worker thread). For custom async reports, `AsyncReportCreator` mirrors
`ReportCreator`.

```python
from mpt_extension_contrib.reports import publish_xlsx_to_confluence_async

uploaded = await publish_xlsx_to_confluence_async(
    async_client, settings, row_mapper=to_row, headers=HEADERS
)
```

## 3. Compose a different report

For any other report, assemble the building blocks directly. `ReportCreator`
works against any queryable Marketplace collection (orders, subscriptions,
agreements, ...):

```python
from mpt_api_client.rql import RQLQuery
from mpt_extension_contrib.reports import (
    EXCEL_MIME_TYPE,
    ConfluenceClient,
    ExcelReportBuilder,
    ReportCreator,
)

creator = ReportCreator(
    client.commerce.subscriptions,
    to_row,
    query=RQLQuery(status__in=["Active"]),
    select=["audit", "parameters"],
)
rows = creator.create()

workbook = ExcelReportBuilder(HEADERS, sheet_name="Subscriptions").build_sheet(rows)

ConfluenceClient(base_url, user, token).attach_content(
    page_id,
    "subscriptions.xlsx",
    workbook,
    content_type=EXCEL_MIME_TYPE,
    comment=f"Total subscriptions {len(rows)}",
)
```

`content_type` is a required argument on `attach_content`; pass `EXCEL_MIME_TYPE`
for `.xlsx` workbooks.
