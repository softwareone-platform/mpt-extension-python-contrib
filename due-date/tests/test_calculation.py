import datetime as dt

from mpt_extension_contrib.due_date import days_until


def test_days_until() -> None:
    due_date = dt.date(2026, 5, 25)
    today = dt.date(2026, 5, 22)

    result = days_until(due_date, today=today)

    assert result == 3
