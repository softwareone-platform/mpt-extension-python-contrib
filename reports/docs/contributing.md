# Contributing

Keep the public API under `mpt_extension_contrib.reports` (exported from
`__init__.py`): the building blocks (`ReportCreator`, `ExcelReportBuilder`,
`ConfluenceClient`, the `QueryableService` protocol) and the turnkey report jobs
(`publish_xlsx_to_confluence`). Keep the modules below the package internal.
Update [architecture.md](architecture.md) when the public API changes.

Keep the generic building blocks free of product-specific business logic: the
caller supplies the column layout (the `ExcelReportBuilder` headers plus the
row mapper) and the RQL filter. Add each new report as its own module under the
package (for example `pending_orders.py`), composing the building blocks rather
than baking vendor-specific fields into them.

Use package-scoped validation with `pkg=reports`. Follow the
repository-wide [contributing workflow](../../docs/contributing.md) for
dependency changes, validation commands, and pre-commit expectations.
