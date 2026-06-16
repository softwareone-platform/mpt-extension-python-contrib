import datetime as dt


def days_until(due_date: dt.date, *, today: dt.date | None = None) -> int:
    """Return the number of days from today until the due date."""
    baseline = today or dt.datetime.now(tz=dt.UTC).date()
    return (due_date - baseline).days
