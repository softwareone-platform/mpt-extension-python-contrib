from typing import override

import pytest
from mpt_extension_contrib.phase_step import phase_gate_step
from mpt_extension_sdk.errors.step import SkipStepError
from mpt_extension_sdk.pipeline import BaseStep

EXPECTED_PHASE = "createSubscription"
OTHER_PHASE = "checkOnboardStatus"


class PlainStep(BaseStep):
    """A step that does not subclass PhaseGatedStep, wrapped by the gate helper."""

    @override
    async def process(self, context):
        """No-op; patched with a mock in tests."""


def test_phase_gate_step_preserves_name():
    gated = phase_gate_step(PlainStep, EXPECTED_PHASE)

    result = gated.__name__

    assert result == "PlainStep"


async def test_phase_gate_step_runs_when_matching(
    order_context_factory, phase_parameter_factory, mocker
):
    context = order_context_factory(fulfillment=[phase_parameter_factory(EXPECTED_PHASE)])
    gated_class = phase_gate_step(PlainStep, EXPECTED_PHASE)
    gated_step = gated_class()
    process = mocker.patch.object(gated_step, "process")

    await gated_step.run(context)

    process.assert_awaited_once()


async def test_phase_gate_step_skips_when_not_matching(
    order_context_factory, phase_parameter_factory, mocker
):
    context = order_context_factory(fulfillment=[phase_parameter_factory(OTHER_PHASE)])
    gated_class = phase_gate_step(PlainStep, EXPECTED_PHASE)
    gated_step = gated_class()
    process = mocker.patch.object(gated_step, "process")

    with pytest.raises(SkipStepError):
        await gated_step.run(context)

    process.assert_not_awaited()


async def test_phase_gate_step_advances_after_success(
    order_context_factory, phase_parameter_factory
):
    context = order_context_factory(fulfillment=[phase_parameter_factory(EXPECTED_PHASE)])
    orders = context.mpt_api_service.orders
    gated_class = phase_gate_step(PlainStep, EXPECTED_PHASE, next_phase="checkOnboard")
    gated_step = gated_class()

    await gated_step.run(context)

    orders.update.assert_awaited_once()


async def test_phase_gate_step_no_advance_when_unset(
    order_context_factory, phase_parameter_factory
):
    context = order_context_factory(fulfillment=[phase_parameter_factory(EXPECTED_PHASE)])
    orders = context.mpt_api_service.orders
    gated_class = phase_gate_step(PlainStep, EXPECTED_PHASE)
    gated_step = gated_class()

    await gated_step.run(context)

    orders.update.assert_not_awaited()


async def test_phase_gate_step_no_advance_on_failure(
    order_context_factory, phase_parameter_factory, mocker
):
    context = order_context_factory(fulfillment=[phase_parameter_factory(EXPECTED_PHASE)])
    orders = context.mpt_api_service.orders
    gated_class = phase_gate_step(PlainStep, EXPECTED_PHASE, next_phase="checkOnboard")
    gated_step = gated_class()
    mocker.patch.object(PlainStep, "process", side_effect=RuntimeError)

    with pytest.raises(RuntimeError):
        await gated_step.run(context)

    orders.update.assert_not_awaited()
