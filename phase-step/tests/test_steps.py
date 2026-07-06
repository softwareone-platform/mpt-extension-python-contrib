from typing import override

import pytest
from mpt_extension_contrib.phase_step import (
    PhaseGatedStep,
    advance_phase,
    require_phase,
)
from mpt_extension_sdk.errors.step import SkipStepError
from mpt_extension_sdk.pipeline import OrderContext
from pydantic import ValidationError

EXPECTED_PHASE = "createSubscription"
OTHER_PHASE = "checkOnboardStatus"
SECOND_PHASE = "createExistingSubscription"


class SampleGatedStep(PhaseGatedStep):
    """Concrete gated step whose ``process`` is patched with a mock in tests."""

    @override
    async def process(self, context: OrderContext) -> None:
        """No-op; tests patch this to assert whether it was awaited."""


class SampleGatedStepWithPre(SampleGatedStep):
    """Gated step with its own ``pre`` guard, run after the phase check."""

    def __init__(self, expected_phases, after_super_pre) -> None:
        super().__init__(expected_phases)
        self._after_super_pre = after_super_pre

    @override
    async def pre(self, context: OrderContext) -> None:
        await super().pre(context)
        await self._after_super_pre(context)


@pytest.mark.parametrize(
    ("stored", "expected"),
    [
        (EXPECTED_PHASE, EXPECTED_PHASE),
        (SECOND_PHASE, [EXPECTED_PHASE, SECOND_PHASE]),
    ],
)
def test_require_phase_passes_when_matching(
    order_context_factory, phase_parameter_factory, stored, expected
):
    context = order_context_factory(fulfillment=[phase_parameter_factory(stored)])

    result = require_phase(context, expected)

    assert result is None


@pytest.mark.parametrize(
    ("stored", "expected", "match"),
    [
        (OTHER_PHASE, EXPECTED_PHASE, r"checkOnboardStatus.*createSubscription"),
        (OTHER_PHASE, [EXPECTED_PHASE, SECOND_PHASE], r"one of"),
        (None, EXPECTED_PHASE, None),
    ],
)
def test_require_phase_skips_when_not_matching(
    order_context_factory, phase_parameter_factory, stored, expected, match
):
    fulfillment = [] if stored is None else [phase_parameter_factory(stored)]
    context = order_context_factory(fulfillment=fulfillment)

    with pytest.raises(SkipStepError, match=match):
        require_phase(context, expected)


@pytest.mark.parametrize("invalid", ["", [], ["createSubscription", ""]])
def test_gated_step_rejects_invalid_phase(invalid):
    with pytest.raises(ValidationError):
        SampleGatedStep(invalid)


@pytest.mark.parametrize(
    ("argument", "expected"),
    [
        (EXPECTED_PHASE, [EXPECTED_PHASE]),
        ([EXPECTED_PHASE, SECOND_PHASE], [EXPECTED_PHASE, SECOND_PHASE]),
    ],
)
def test_gated_step_exposes_phases(argument, expected):
    step = SampleGatedStep(argument)

    result = step.expected_phases

    assert result == expected


@pytest.mark.parametrize(
    ("stored", "expected"),
    [
        (EXPECTED_PHASE, EXPECTED_PHASE),
        (SECOND_PHASE, [EXPECTED_PHASE, SECOND_PHASE]),
    ],
)
async def test_gated_step_processes_when_matching(
    order_context_factory, phase_parameter_factory, mocker, stored, expected
):
    context = order_context_factory(fulfillment=[phase_parameter_factory(stored)])
    step = SampleGatedStep(expected)
    process = mocker.patch.object(step, "process")

    await step.run(context)

    process.assert_awaited_once()


@pytest.mark.parametrize("stored", [OTHER_PHASE, None])
async def test_gated_step_skips_when_not_matching(
    order_context_factory, phase_parameter_factory, mocker, stored
):
    fulfillment = [] if stored is None else [phase_parameter_factory(stored)]
    context = order_context_factory(fulfillment=fulfillment)
    step = SampleGatedStep(EXPECTED_PHASE)
    process = mocker.patch.object(step, "process")

    with pytest.raises(SkipStepError):
        await step.run(context)

    process.assert_not_awaited()


async def test_subclass_pre_runs_after_check(
    order_context_factory, phase_parameter_factory, mocker
):
    context = order_context_factory(fulfillment=[phase_parameter_factory(EXPECTED_PHASE)])
    after_super_pre = mocker.AsyncMock()
    step = SampleGatedStepWithPre(EXPECTED_PHASE, after_super_pre)

    await step.run(context)

    after_super_pre.assert_awaited_once()


async def test_subclass_pre_skipped_on_mismatch(
    order_context_factory, phase_parameter_factory, mocker
):
    context = order_context_factory(fulfillment=[phase_parameter_factory(OTHER_PHASE)])
    after_super_pre = mocker.AsyncMock()
    step = SampleGatedStepWithPre(EXPECTED_PHASE, after_super_pre)

    with pytest.raises(SkipStepError):
        await step.run(context)

    after_super_pre.assert_not_awaited()


async def test_advance_phase_persists(order_context_factory, phase_parameter_factory):
    context = order_context_factory(fulfillment=[phase_parameter_factory(EXPECTED_PHASE)])
    orders = context.mpt_api_service.orders

    await advance_phase(context, "completed")

    orders.update.assert_awaited_once()


async def test_advance_phase_writes_new_phase(order_context_factory, phase_parameter_factory):
    context = order_context_factory(fulfillment=[phase_parameter_factory(EXPECTED_PHASE)])
    orders = context.mpt_api_service.orders
    order_id = context.order_id
    expected = context.order.parameters.with_fulfillment_value("phase", "completed").to_dict()

    await advance_phase(context, "completed")

    orders.update.assert_awaited_once_with(order_id, {"parameters": expected})


async def test_advance_phase_refreshes_order(order_context_factory, phase_parameter_factory):
    context = order_context_factory(fulfillment=[phase_parameter_factory(EXPECTED_PHASE)])
    orders = context.mpt_api_service.orders

    await advance_phase(context, "completed")

    orders.get_by_id.assert_awaited_once()
