# Contributing

Keep the public API under `mpt_extension_contrib.order_status` limited to the
pipeline steps, the `resolve_template` helper, and the `OrderStatus` enum.
Add new statuses to `OrderStatus` rather than passing raw strings, and keep the
steps free of product-specific business logic. Update
[architecture.md](architecture.md) when the public API changes.

Use package-scoped validation with `pkg=order-status`. Follow the
repository-wide [contributing workflow](../../docs/contributing.md) for
dependency changes, validation commands, and pre-commit expectations.
