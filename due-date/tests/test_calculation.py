import datetime as dt

import pytest
from freezegun import freeze_time
from mpt_extension_contrib.due_date.calculation import (
    compute_due_date,
    format_due_date,
    is_due_date_reached,
    parse_due_date,
)


def test_compute_due_date_with_explicit_start():
    start = dt.date(2026, 6, 1)

    result = compute_due_date(days=10, start=start)

    assert result == dt.date(2026, 6, 11)


@freeze_time("2026-06-15")
def test_compute_due_date_defaults_to_today():
    result = compute_due_date(days=5)

    assert result == dt.date(2026, 6, 20)


@pytest.mark.parametrize(
    ("due_date", "today", "expected"),
    [
        (dt.date(2026, 6, 10), dt.date(2026, 6, 9), False),
        (dt.date(2026, 6, 10), dt.date(2026, 6, 10), False),
        (dt.date(2026, 6, 10), dt.date(2026, 6, 11), True),
    ],
)
def test_is_due_date_reached(due_date, today, expected):
    result = is_due_date_reached(due_date, today=today)

    assert result is expected


@freeze_time("2026-06-15")
def test_is_due_date_reached_default_today():
    result = is_due_date_reached(dt.date(2026, 6, 14))

    assert result is True


def test_parse_and_format_round_trip():
    due_date = dt.date(2026, 6, 10)

    result = parse_due_date(format_due_date(due_date))

    assert result == due_date
