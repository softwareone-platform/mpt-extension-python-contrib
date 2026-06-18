import datetime as dt

from mpt_extension_contrib.due_date.calculation import format_due_date, parse_due_date
from mpt_extension_sdk.models import ParameterBag


def get_due_date(parameter_bag: ParameterBag, parameter_external_id: str) -> dt.date | None:
    """Return the due date stored in the fulfillment parameter, or ``None``.

    Args:
        parameter_bag: The order parameters.
        parameter_external_id: External id of the due-date fulfillment parameter.

    Returns:
        The stored due date, or ``None`` when it is not set.
    """
    raw_value = parameter_bag.get_fulfillment_value(parameter_external_id)
    return parse_due_date(raw_value) if raw_value else None


def set_due_date(
    parameter_bag: ParameterBag,
    due_date: dt.date | None,
    parameter_external_id: str,
) -> ParameterBag:
    """Return a copy with the due-date parameter set to an explicit date.

    Passing ``None`` clears the parameter.

    Args:
        parameter_bag: The order parameters.
        due_date: The due date to store, or ``None`` to clear it.
        parameter_external_id: External id of the due-date fulfillment parameter.

    Returns:
        A copy of the parameters with the due date applied.
    """
    stored_value = format_due_date(due_date) if due_date else None
    return parameter_bag.with_fulfillment_value(parameter_external_id, stored_value)


def reset_due_date(parameter_bag: ParameterBag, parameter_external_id: str) -> ParameterBag:
    """Return a copy with the due-date parameter cleared."""
    return set_due_date(parameter_bag, None, parameter_external_id)
