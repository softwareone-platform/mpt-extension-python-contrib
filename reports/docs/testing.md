# Testing

Tests for `mpt-extension-contrib-reports` live under [`../tests/`](../tests):

- `test_report.py` — `ReportCreator` (and `AsyncReportCreator` against a fake
  async service) against a fake queryable service: applying the RQL filter and
  `select`, mapping each resource payload to a row, the defaults when
  `query`/`select` are omitted, treating an empty `select` the same as unset,
  and — with no `row_mapper` — inferring headers and flattening nested dicts into
  dotted columns (including ragged payloads).
- `test_excel.py` — `ExcelReportBuilder`: `build_sheet` writes a bold header
  row, the data rows, and the auto-filter (including the header-only case);
  `build_multi_sheet` creates one sheet per definition and rejects an empty
  list; `save` writes bytes to a path.
- `test_confluence.py` — `ConfluenceClient` against a monkeypatched
  `atlassian.Confluence`: credentials and arguments are forwarded, `comment`
  defaults to `None`, and the call returns `False` for both
  `requests.exceptions.RequestException` and `atlassian.errors.ApiError`.
- `test_pending_orders.py` — `publish_xlsx_to_confluence` end to end with a fake
  order client, a fake settings object, and a monkeypatched `ConfluenceClient`:
  it reads the Confluence config and page id from settings, filters on
  `PENDING_ORDER_STATUSES`, maps the rows, and attaches a date-stamped
  `orders-DD-MM-YYYY.xlsx` with the Excel MIME type and a total-count comment,
  propagating the upload result. It also covers the no-config inferred path,
  that mismatched `row_mapper`/`headers` raise `ValueError`, and the async job
  (`publish_xlsx_to_confluence_async`) over a fake async orders service.

The pending-orders job reads the clock for its filename, so its test freezes
time with `freezegun` to keep the date deterministic.

Use package-scoped test commands with `pkg=reports`. Coverage must stay at
the repository threshold. See the repository-wide
[testing strategy](../../docs/testing.md).
