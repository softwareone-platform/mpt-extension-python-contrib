from mpt_extension_contrib.fixtures import OrderFactory, Scenarios, parameter_bag
from mpt_extension_sdk.models import Order

ORDERS = Scenarios(
    OrderFactory,
    {
        "purchase": {"type": "Purchase"},
        "change": {"type": "Change", "status": "Processing"},
        "with_params": {
            "type": "Purchase",
            "parameters": parameter_bag(ordering={"accountType": "New"}),
        },
    },
)

order = ORDERS.fixture()


def test_build_applies_spec_fields() -> None:
    result = ORDERS.build("change")

    assert result.type == "Change"
    assert result.status == "Processing"


def test_build_passes_overrides() -> None:
    result = ORDERS.build("purchase", status="Querying")

    assert result.status == "Querying"


def test_parameters_are_just_a_field() -> None:
    result = ORDERS.build("with_params")

    assert result.parameters.get_ordering_value("accountType") == "New"


def test_cases_uses_names_as_ids() -> None:
    result = ORDERS.cases()

    assert [case.id for case in result] == ["purchase", "change", "with_params"]


def test_cases_filters_with_only() -> None:
    result = ORDERS.cases(only=["change"])

    assert [case.id for case in result] == ["change"]


def test_cases_yields_built_models() -> None:
    result = ORDERS.cases(only=["change"])

    assert result[0].values[0].type == "Change"


def test_fixture_runs_per_case(order: Order) -> None:
    result = order.type

    assert result in {"Purchase", "Change"}
