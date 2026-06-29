# mpt-extension-contrib-reports

Reusable building blocks for generating tabular vendor reports and publishing
them to Confluence, for SoftwareONE MPT extensions built on the Extension SDK.

It extracts the daily pending-order report previously implemented inside the AWS
extension into a shared library, so any extension can publish business
observability without re-implementing it. The column layout and Confluence
credentials are supplied by the caller, so no product-specific business logic
lives in the library.

See [AGENTS.md](AGENTS.md) for the module documentation map.

## Install

```bash
pip install mpt-extension-contrib-reports
```

Compatible with the Extension SDK `>= 6.0.0`; it depends on `mpt-api-client`
(the SDK's Marketplace API client) plus `openpyxl`, `requests`, and
`atlassian-python-api`, which are pulled in as dependencies.

## Public API

`mpt_extension_contrib.reports` exposes:

| Object | Purpose |
| --- | --- |
| `publish_xlsx_to_confluence` | Turnkey daily pending-orders report → Confluence page (sync `MPTClient`). |
| `publish_xlsx_to_confluence_async` | Async variant of the job for an `AsyncMPTClient`. |
| `PendingOrdersReportSettings` | `Protocol` for the settings that job reads (Confluence config + page id). |
| `ReportCreator` | Fetch resources by RQL query and build a `Report` (headers + rows). |
| `AsyncReportCreator` | Async counterpart of `ReportCreator` for an `AsyncMPTClient` collection. |
| `Report` | The built report: `headers` and `rows` (returned by `create()`). |
| `ExcelReportBuilder` | Turn headers and rows into `.xlsx` bytes. |
| `ConfluenceClient` | Attach file bytes to a Confluence page. |
| `QueryableService`, `AsyncQueryableService` | `Protocol`s for the (sync/async) collection the creators accept. |
| `PENDING_ORDER_STATUSES` | The order statuses (`Querying`, `Processing`) treated as pending. |
| `EXCEL_MIME_TYPE` | MIME type for `.xlsx` workbooks, passed as `content_type` when attaching them. |
| `ReportRow`, `ReportRows`, `RowMapper`, `SheetDefinition` | Public type aliases. |

## Usage

### Daily pending-orders report

`publish_xlsx_to_confluence` packages the original AWS use case: it fetches
every pending order, builds a workbook, and attaches it to a Confluence page
under a date-stamped filename (`orders-<DD-MM-YYYY>.xlsx`) with a
`Total orders <N>` comment. The Confluence config and target page come from your
extension settings, which must satisfy the `PendingOrdersReportSettings`
protocol:

```python
confluence_base_url: str
confluence_user: str
confluence_token: str
pending_orders_information_report_page_id: str
```

You pass the API client, the settings, and the column layout:

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
    client,
    settings,  # satisfies PendingOrdersReportSettings
    row_mapper=to_row,
    headers=HEADERS,
)
```

The helper reads the Confluence base URL, credentials, and page id from
`settings`, queries the client's `commerce.orders` collection, and bakes in the
pending-status filter, the workbook build (sheet name included), the filename,
and the comment.

`row_mapper` and `headers` are a pair: pass both to control the exact column
layout, or omit both for a quick report whose columns are inferred from the
order fields (nested objects flattened into dotted columns like `client.id`,
`audit.created.at`). Providing only one raises `ValueError`. `select` (default
`("audit", "parameters")`) controls which order attributes are fetched — narrow
it to match a custom `row_mapper`, or to limit what an inferred report exposes.

For an `AsyncMPTClient`, use `publish_xlsx_to_confluence_async` — same arguments
and behaviour, fetched with `async for` (the blocking Confluence upload runs in a
worker thread):

```python
uploaded = await publish_xlsx_to_confluence_async(
    async_client, settings, row_mapper=to_row, headers=HEADERS
)
```

### Building blocks

For other reports, compose the pieces directly with `ReportCreator`:

```python
from mpt_api_client.rql import RQLQuery
from mpt_extension_contrib.reports import ExcelReportBuilder, ReportCreator

# Any queryable Marketplace collection works, e.g. `client.commerce.subscriptions`.
creator = ReportCreator(
    client.commerce.orders,
    to_row,
    query=RQLQuery(status__in=["Querying", "Processing"]),
    select=["audit", "parameters"],
)
report = creator.create()  # Report(headers, rows)
workbook = ExcelReportBuilder(HEADERS, sheet_name="Pending Orders").build_sheet(report.rows)
```

## Documentation

- [Usage](docs/usage.md)
- [Architecture](docs/architecture.md)
- [Contributing](docs/contributing.md)
- [Testing](docs/testing.md)
- [Releases](docs/releases.md)
