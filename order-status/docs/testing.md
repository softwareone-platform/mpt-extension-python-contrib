# Testing

Tests for `mpt-extension-contrib-order-status` live under [`../tests/`](../tests):

- `test_templates.py` — `resolve_template`: returns the named template when the
  SDK service finds it, without logging; falls back to the default and logs the
  fallback when the requested name is not matched; logs the same fallback
  message when the product has no template at all for the status; and does not
  log when no name was requested (the default was asked for on purpose).
- `test_steps.py` — the two pipeline steps against a real `OrderContext` (built
  by the module `order_context_factory` fixture, with autospec'd `orders` and
  `templates` services): `CompleteOrder` completes the order and refreshes the
  context when a template resolves, raises `SkipStepError` when the order is
  already `Completed` without calling `orders.complete`, and raises
  `StopStepError` when the product has no completion template;
  `StartOrderProcessing` sets and persists the template when none is set or it
  differs from the current one, leaves the order untouched when the resolved
  template already matches, and is a no-op when the product has no processing
  template.

`tests/conftest.py` builds the `OrderContext` directly (order `status`,
`product`, `template`, and empty `parameters`) rather than reusing the
repository-wide `order_context_factory`, because these steps need order fields
(`status`, `product`, `template`) that fixture does not set.

Use package-scoped test commands with `pkg=order-status`. Coverage must stay at
the repository threshold. See the repository-wide
[testing strategy](../../docs/testing.md).
