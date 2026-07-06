from typing import Annotated, Protocol, cast, override

from mpt_extension_sdk.errors.step import SkipStepError
from mpt_extension_sdk.pipeline import BaseStep, OrderContext
from pydantic import Field, StringConstraints, validate_call

ExpectedPhase = Annotated[str, StringConstraints(min_length=1)]
ExpectedPhases = ExpectedPhase | Annotated[list[ExpectedPhase], Field(min_length=1)]


class PhaseStepSettings(Protocol):
    """Extension settings contract required by the phase gating helpers.

    An extension's ``ExtensionSettings`` satisfies this structurally by exposing
    a ``phase_parameter`` string; it may also inherit this protocol to have
    the contract checked explicitly.
    """

    phase_parameter: str


def _phase_parameter(context: OrderContext) -> str:
    """Return the phase parameter external id from the extension settings."""
    return cast(PhaseStepSettings, context.ext_settings).phase_parameter


@validate_call
def _normalize_phases(expected_phases: ExpectedPhases) -> list[str]:
    """Return the expected phases as a non-empty list of non-empty strings."""
    if isinstance(expected_phases, str):
        return [expected_phases]
    return list(expected_phases)


def _format_expected(phases: list[str]) -> str:
    """Render the expected phases for a skip message."""
    if len(phases) == 1:
        return f"'{phases[0]}'"
    joined = ", ".join(f"'{phase}'" for phase in phases)
    return f"one of {joined}"


def require_phase(context: OrderContext, expected_phases: ExpectedPhases) -> None:
    """Skip the current step unless the order phase is one of the expected ones.

    Reads the provisioning phase from the fulfillment parameter named by the
    extension settings field ``phase_parameter`` and checks it against
    ``expected_phases``. Call it from a step ``pre()`` hook; the pipeline
    handles the raised skip and continues with the next step.

    Args:
        context: The order pipeline context.
        expected_phases: A phase, or a non-empty list of phases, the step
            runs for.

    Raises:
        SkipStepError: When the current phase is not one of the expected ones.
    """
    phases = _normalize_phases(expected_phases)
    current_phase = context.order.parameters.get_fulfillment_value(_phase_parameter(context))
    if current_phase not in phases:
        raise SkipStepError(
            f"current phase is '{current_phase}', expected {_format_expected(phases)}"
        )


async def advance_phase(context: OrderContext, phase: str) -> None:
    """Persist a new provisioning phase on the order.

    Convenience for the common "advance the phase" write: it sets the phase
    fulfillment parameter (named by the extension settings field
    ``phase_parameter``) on an updated ``ParameterBag``, persists it through
    ``context.mpt_api_service.orders.update``, and then refreshes
    ``context.order``. Call it from ``process()`` at the point the step decides
    to move forward; gating (the read) stays in ``pre()``.

    It refreshes ``context.order`` (via ``context.refresh_order()``) after the
    write so the persisted and in-memory phase stay consistent: a later gated
    step in the same pipeline run reads the new phase from ``context.order`` and
    gates correctly, instead of seeing the stale value and being skipped. This is
    the read-after-write case the SDK pipeline-steps guideline refreshes for. The
    refresh is one extra fetch; a caller that must avoid it (advancing as the last
    step, or batching the phase into a larger order update) can drop to
    ``context.order.parameters.with_fulfillment_value(...)`` plus its own
    ``orders.update`` instead.

    Args:
        context: The order pipeline context.
        phase: The provisioning phase to store.
    """
    parameter_bag = context.order.parameters.with_fulfillment_value(
        _phase_parameter(context), phase
    )
    await context.mpt_api_service.orders.update(
        context.order_id,
        {"parameters": parameter_bag.to_dict()},
    )
    await context.refresh_order()


class PhaseGatedStep(BaseStep):
    """Base step that runs only for one of a set of provisioning phases.

    A gated drop-in replacement for the SDK ``BaseStep``: subclass it and
    implement ``process()`` for a phase-gated step, the same way you subclass
    ``BaseStep`` for a plain one. The expected phases are a constructor
    argument, so they live in the pipeline definition rather than the class
    body. ``pre()`` skips the step (via :func:`require_phase`) unless the order
    phase matches.

    A subclass that needs its own ``pre()`` logic overrides it and calls
    ``await super().pre(context)`` explicitly, making the check order visible
    in the method body.

    The phase parameter external id comes from the extension settings field
    ``phase_parameter`` (``context.ext_settings``).
    """

    def __init__(self, expected_phases: ExpectedPhases) -> None:
        self._expected_phases = _normalize_phases(expected_phases)

    @property
    def expected_phases(self) -> list[str]:
        """The provisioning phases this step runs for."""
        return list(self._expected_phases)

    @override
    async def pre(self, context: OrderContext) -> None:
        """Skip the step unless the order phase is one of the expected ones."""
        require_phase(context, self._expected_phases)
