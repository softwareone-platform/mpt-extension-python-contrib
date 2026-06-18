import pytest
from freezegun import freeze_time
from mpt_extension_contrib.due_date import (
    DueDateReachedError,
    EnforceDueDate,
    ResetDueDate,
    SetDueDate,
)
from mpt_extension_sdk.errors.step import SkipStepError
from mpt_extension_sdk.pipeline import OrderStatusActionType
from pydantic import ValidationError


def test_set_due_date_rejects_negative_days():
    with pytest.raises(ValidationError):
        SetDueDate(days=-1)


async def test_set_due_date_persists_when_unset(order_context_factory):
    context = order_context_factory()
    orders = context.mpt_api_service.orders

    await SetDueDate(days=10).run(context)

    orders.update.assert_awaited_once()


async def test_set_due_date_refreshes_order(order_context_factory):
    context = order_context_factory()
    orders = context.mpt_api_service.orders

    await SetDueDate(days=10).run(context)

    orders.get_by_id.assert_awaited_once()


async def test_set_due_date_skips_when_already_set(
    order_context_factory, due_date_parameter_factory
):
    context = order_context_factory(fulfillment=[due_date_parameter_factory("2026-07-01")])
    orders = context.mpt_api_service.orders

    with pytest.raises(SkipStepError):
        await SetDueDate(days=10).run(context)

    orders.update.assert_not_awaited()


@freeze_time("2026-06-15")
async def test_enforce_declares_fail_when_reached(
    order_context_factory, due_date_parameter_factory
):
    context = order_context_factory(fulfillment=[due_date_parameter_factory("2026-06-01")])

    with pytest.raises(DueDateReachedError):
        await EnforceDueDate().run(context)

    assert context.order_state.action.target_status == OrderStatusActionType.FAIL


@freeze_time("2026-06-15")
async def test_enforce_continues_before_due_date(order_context_factory, due_date_parameter_factory):
    context = order_context_factory(fulfillment=[due_date_parameter_factory("2026-07-01")])

    await EnforceDueDate().run(context)

    assert context.order_state.action is None


async def test_enforce_skips_when_unset(order_context_factory):
    context = order_context_factory()

    with pytest.raises(SkipStepError):
        await EnforceDueDate().run(context)


async def test_reset_due_date_persists_clear(order_context_factory, due_date_parameter_factory):
    context = order_context_factory(fulfillment=[due_date_parameter_factory("2026-06-10")])
    orders = context.mpt_api_service.orders

    await ResetDueDate().run(context)

    orders.update.assert_awaited_once()


async def test_reset_due_date_skips_when_unset(order_context_factory):
    context = order_context_factory()
    orders = context.mpt_api_service.orders

    with pytest.raises(SkipStepError):
        await ResetDueDate().run(context)

    orders.update.assert_not_awaited()
