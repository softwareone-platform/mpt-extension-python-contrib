# Testing

Tests for `mpt-extension-contrib-due-date` live under [`../tests/`](../tests):

- `test_calculation.py` — date math: computing a due date from `days` (explicit
  start and the UTC-today default) and the reached/not-reached/boundary cases.
- `test_parameters.py` — reading, setting (explicit date), clearing, and
  overwriting the due-date fulfillment parameter on a `ParameterBag`.
- `test_steps.py` — the three pipeline steps against a real `OrderContext`
  (built by the shared `order_context_factory` fixture, with an autospec'd
  `mpt_api_service`): `SetDueDate` persists once and is skipped when the due date
  is already set; `EnforceDueDate` fails the order once the deadline has passed
  and is skipped when the due date is unset; `ResetDueDate` clears and persists,
  and is skipped when there is nothing to clear.

Tests pass dates explicitly; where a step reads the clock by default, the test
freezes time with `freezegun` so behaviour stays deterministic.

Use package-scoped test commands with `pkg=due-date`. Coverage must stay at the
repository threshold. See the repository-wide
[testing strategy](../../docs/testing.md).
