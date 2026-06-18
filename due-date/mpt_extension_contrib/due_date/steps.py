from typing import Protocol, cast, override

from mpt_extension_contrib.due_date.calculation import (
    compute_due_date,
    format_due_date,
    is_due_date_reached,
)
from mpt_extension_contrib.due_date.parameters import get_due_date, reset_due_date, set_due_date
from mpt_extension_sdk.errors.step import SkipStepError, StopStepError
from mpt_extension_sdk.pipeline import (
    BaseStep,
    OrderContext,
    OrderStatusAction,
    OrderStatusActionType,
    refresh_order,
)
from pydantic import NonNegativeInt, validate_call


class DueDateSettings(Protocol):
    """Extension settings contract required by the due-date steps.

    An extension's ``ExtensionSettings`` satisfies this structurally by exposing
    a ``due_date_parameter`` string; it may also inherit this protocol to have
    the contract checked explicitly.
    """

    due_date_parameter: str


class DueDateReachedError(StopStepError):
    """Raised by :class:`EnforceDueDate` when the due date has been reached.

    It is a :class:`StopStepError` subclass, so the pipeline stops exactly as
    for any other stop, while a pipeline hook or error handler can recognise a
    due-date failure with ``isinstance(error, DueDateReachedError)`` and react
    to it specifically.
    """


def _due_date_parameter(context: OrderContext) -> str:
    """Return the due-date parameter external id from the extension settings."""
    return cast(DueDateSettings, context.ext_settings).due_date_parameter


class SetDueDate(BaseStep):
    """Set and persist the order due date when it is not set yet.

    On the first run it computes ``today + days``, persists it on the order
    through ``mpt_api_service``, and refreshes the context order so later steps
    read the stored due date. The step is skipped once the due date is set, so
    the deadline stays stable across reprocessing.

    The due-date parameter external id comes from the extension settings field
    ``due_date_parameter`` (``context.ext_settings``).
    """

    @validate_call
    def __init__(self, *, days: NonNegativeInt) -> None:
        self._days = days

    @override
    async def pre(self, context: OrderContext) -> None:
        """Skip the step when the due date is already set."""
        if get_due_date(context.order.parameters, _due_date_parameter(context)) is not None:
            raise SkipStepError("due date is already set")

    @override
    @refresh_order
    async def process(self, context: OrderContext) -> None:
        """Persist the computed due date, then refresh the order."""
        external_id = _due_date_parameter(context)
        due_date = compute_due_date(days=self._days)
        parameter_bag = set_due_date(context.order.parameters, due_date, external_id)
        await context.mpt_api_service.orders.update(
            context.order_id,
            {"parameters": parameter_bag.to_dict()},
        )


class EnforceDueDate(BaseStep):
    """Declare a fail action once the order due date has been reached.

    Reads the due date from the fulfillment parameter named by the extension
    settings field ``due_date_parameter``. When the deadline has passed it
    records a ``Failed`` order action on ``context.order_state`` and stops the
    pipeline; the extension's pipeline ``on_step_stopped``/``on_step_failed``
    hook applies the transition (see the SDK pipeline-hooks contract). The step
    is skipped while the due date is unset and is a no-op while it is still in
    the future.
    """

    @override
    async def pre(self, context: OrderContext) -> None:
        """Skip the step when there is no due date to enforce."""
        if get_due_date(context.order.parameters, _due_date_parameter(context)) is None:
            raise SkipStepError("due date is not set")

    @override
    async def process(self, context: OrderContext) -> None:
        """Declare a fail action and stop the pipeline when the due date passed.

        Args:
            context: The order pipeline context.

        Raises:
            DueDateReachedError: When the due date has been reached.
        """
        due_date = get_due_date(context.order.parameters, _due_date_parameter(context))
        if due_date is None or not is_due_date_reached(due_date):
            return

        message = f"Order processing due date {format_due_date(due_date)} has been reached."
        context.order_state.action = OrderStatusAction(
            target_status=OrderStatusActionType.FAIL,
            message=message,
            status_notes={"message": message},
        )
        raise DueDateReachedError(message)


class ResetDueDate(BaseStep):
    """Clear and persist the order due date.

    Run this before completing an order so its due-date parameter is empty,
    leaving a clean state for any future order on the same agreement. The step
    is skipped when the due date is already unset.

    The due-date parameter external id comes from the extension settings field
    ``due_date_parameter`` (``context.ext_settings``).
    """

    @override
    async def pre(self, context: OrderContext) -> None:
        """Skip the step when there is no due date to clear."""
        if get_due_date(context.order.parameters, _due_date_parameter(context)) is None:
            raise SkipStepError("due date is not set")

    @override
    async def process(self, context: OrderContext) -> None:
        """Persist a cleared due date."""
        external_id = _due_date_parameter(context)
        parameter_bag = reset_due_date(context.order.parameters, external_id)
        await context.mpt_api_service.orders.update(
            context.order_id,
            {"parameters": parameter_bag.to_dict()},
        )
