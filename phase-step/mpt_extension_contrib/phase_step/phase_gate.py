from typing import override

from mpt_extension_contrib.phase_step.steps import (
    ExpectedPhases,
    _normalize_phases,  # ruff:ignore[import-private-name]  # same-package internal helper
    advance_phase,
    require_phase,
)
from mpt_extension_sdk.pipeline import BaseStep, OrderContext


def phase_gate_step(
    cls: type[BaseStep],
    expected_phases: ExpectedPhases,
    next_phase: str | None = None,
) -> type[BaseStep]:
    """Return a subclass of ``cls`` gated on ``expected_phases``.

    Use it to phase-gate a step class that cannot subclass :class:`PhaseGatedStep`
    directly (for example a step defined elsewhere). The returned subclass runs
    the phase check in ``pre()`` before the wrapped step's own ``pre()``.

    When ``next_phase`` is given, the returned step advances the order to that
    phase (via :func:`advance_phase`) after the wrapped step's ``process()``
    completes successfully. This covers the simple linear transition; for a next
    phase that depends on the step's own logic, subclass :class:`PhaseGatedStep`
    and advance explicitly inside ``process()`` instead.

    Prefer subclassing :class:`PhaseGatedStep` when you own the step; this helper
    exists for the case where you only have the class to wrap.

    Args:
        cls: The step class to gate.
        expected_phases: A phase, or a non-empty list of phases, the step runs for.
        next_phase: The phase to advance to after a successful ``process()``, or
            ``None`` to leave the phase unchanged.

    Returns:
        A ``cls`` subclass that skips unless the order phase matches.
    """
    phases = _normalize_phases(expected_phases)

    # ``cls`` is only known at runtime, so mypy cannot verify the base class.
    class _Gated(cls):  # type: ignore[misc, valid-type]  # noqa: WPS431
        @override
        async def pre(self, context: OrderContext) -> None:
            require_phase(context, phases)
            await super().pre(context)

        @override
        async def process(self, context: OrderContext) -> None:
            await super().process(context)
            if next_phase is not None:
                await advance_phase(context, next_phase)

    _Gated.__name__ = cls.__name__
    _Gated.__qualname__ = cls.__qualname__
    return _Gated
