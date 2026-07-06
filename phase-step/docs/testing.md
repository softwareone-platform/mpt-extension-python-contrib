# Testing

Tests for `mpt-extension-contrib-phase-step` live in
[`../tests/test_steps.py`](../tests/test_steps.py) and cover `require_phase`,
`PhaseGatedStep`, and `advance_phase` against a real `OrderContext` (built by
the shared `order_context_factory` fixture, with an autospec'd
`mpt_api_service`):

- a match with a single phase and with one of a list of phases runs the step;
  a mismatch and an unset phase skip it;
- the constructor rejects an empty phase, an empty list, and an empty phase
  inside a list;
- a subclass `pre()` runs its own guard only after the inherited phase check
  passes;
- `advance_phase` persists the new phase through `mpt_api_service.orders.update`
  with the parameter external id taken from the settings.

Assert step execution with a mock, not an instance flag: patch `process` with
`mocker.patch.object(step, "process")` (auto-detected as an `AsyncMock`) and
check `assert_awaited_once()` / `assert_not_awaited()`. The phase parameter is
built with the local `phase_parameter_factory` fixture ([conftest.py](../tests/conftest.py)),
whose external id (`phase`) matches the test `ExtensionSettings`.

Use package-scoped test commands with `pkg=phase-step`. Coverage must stay at
the repository threshold. See the repository-wide
[testing strategy](../../docs/testing.md).
