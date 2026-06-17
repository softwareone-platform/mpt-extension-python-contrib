import datetime as dt

DATE_FORMAT = "%Y-%m-%d"


def compute_due_date(*, days: int, start: dt.date | None = None) -> dt.date:
    """Return the due date ``days`` days after ``start`` (today in UTC by default).

    Args:
        days: Number of days an order may stay in processing.
        start: Day the countdown starts from; defaults to today in UTC.

    Returns:
        The computed due date.
    """
    base = start or dt.datetime.now(tz=dt.UTC).date()
    return base + dt.timedelta(days=days)


def is_due_date_reached(due_date: dt.date, *, today: dt.date | None = None) -> bool:
    """Return whether the due date has passed.

    Args:
        due_date: The order processing deadline.
        today: Day to compare against; defaults to today in UTC.

    Returns:
        ``True`` when ``today`` is strictly after ``due_date``.
    """
    current = today or dt.datetime.now(tz=dt.UTC).date()
    return current > due_date


def format_due_date(due_date: dt.date) -> str:
    """Return the due date rendered as a ``YYYY-MM-DD`` string."""
    return due_date.strftime(DATE_FORMAT)


def parse_due_date(raw_value: str) -> dt.date:
    """Return the date parsed from a ``YYYY-MM-DD`` string (UTC)."""
    return dt.datetime.strptime(raw_value, DATE_FORMAT).replace(tzinfo=dt.UTC).date()
