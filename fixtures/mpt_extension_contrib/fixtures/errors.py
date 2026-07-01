"""MPT API error payload factory.

An MPT error is an API payload rather than an SDK model, so it is built as a
plain dict instead of through polyfactory.
"""

from __future__ import annotations

from typing import Any


def mpt_error_factory(
    status: int,
    title: str,
    detail: str,
    *,
    trace_id: str = "00-traceid-spanid-00",
    field_errors: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an MPT API error payload.

    ``field_errors`` is added under the ``errors`` key only when provided.
    """
    payload: dict[str, Any] = {
        "status": status,
        "title": title,
        "detail": detail,
        "traceId": trace_id,
    }
    if field_errors is not None:
        payload["errors"] = field_errors
    return payload
