import datetime as dt

from mpt_extension_contrib.due_date.parameters import get_due_date, reset_due_date, set_due_date


def test_get_due_date_returns_none_when_unset(parameter_bag_factory):
    result = get_due_date(parameter_bag_factory(), "dueDate")

    assert result is None


def test_get_due_date_parses_stored_value(parameter_bag_factory, due_date_parameter_factory):
    parameter_bag = parameter_bag_factory(fulfillment=[due_date_parameter_factory("2026-06-10")])

    result = get_due_date(parameter_bag, "dueDate")

    assert result == dt.date(2026, 6, 10)


def test_set_due_date_stores_explicit_date(parameter_bag_factory):
    due_date = dt.date(2026, 6, 6)

    result = set_due_date(parameter_bag_factory(), due_date, "dueDate")

    assert get_due_date(result, "dueDate") == due_date


def test_set_due_date_overwrites_existing_value(parameter_bag_factory, due_date_parameter_factory):
    parameter_bag = parameter_bag_factory(fulfillment=[due_date_parameter_factory("2026-06-10")])

    result = set_due_date(parameter_bag, dt.date(2026, 6, 20), "dueDate")

    assert get_due_date(result, "dueDate") == dt.date(2026, 6, 20)


def test_set_due_date_none_clears_value(parameter_bag_factory, due_date_parameter_factory):
    parameter_bag = parameter_bag_factory(fulfillment=[due_date_parameter_factory("2026-06-10")])

    result = set_due_date(parameter_bag, None, "dueDate")

    assert get_due_date(result, "dueDate") is None


def test_reset_due_date_clears_value(parameter_bag_factory, due_date_parameter_factory):
    parameter_bag = parameter_bag_factory(fulfillment=[due_date_parameter_factory("2026-06-10")])

    result = reset_due_date(parameter_bag, "dueDate")

    assert get_due_date(result, "dueDate") is None
