"""Readable demo of the fixtures library on orders and agreements.

Each test reads top-to-bottom as an example; it mirrors docs/usage.md and doubles
as the MPT-22111 demo (fixtures used in a passing test suite).
"""

from mpt_extension_contrib.fixtures import (
    AgreementFactory,
    OrderFactory,
    Scenarios,
    mpt_error_factory,
    parameter_bag,
)


def test_build_a_purchase_order() -> None:
    result = OrderFactory.purchase()

    assert result.type == "Purchase"
    assert result.parameters.ordering == []


def test_inject_product_parameters() -> None:
    order = OrderFactory.purchase(
        parameters=parameter_bag(ordering={"accountType": "New", "mpaId": "123456"}),
    )

    result = order.parameters.get_ordering_value("accountType")

    assert result == "New"


def test_build_an_agreement_with_nested_models() -> None:
    result = AgreementFactory.build()

    assert result.client is not None
    assert result.licensee is not None
    assert result.product is not None


def test_named_scenarios_drive_a_test_matrix() -> None:
    orders = Scenarios(
        OrderFactory,
        {
            "new_purchase": {"type": "Purchase", "status": "Processing"},
            "change": {"type": "Change", "status": "Querying"},
        },
    )

    result = orders.build("change")

    assert result.type == "Change"
    assert result.status == "Querying"


def test_to_dict_bridge_yields_api_shaped_json() -> None:
    order = OrderFactory.purchase()

    result = order.to_dict()

    assert result["type"] == "Purchase"
    assert isinstance(result["parameters"], dict)


def test_mpt_error_payload() -> None:
    result = mpt_error_factory(400, "Bad Request", "Invalid order")

    assert result["status"] == 400
    assert result["title"] == "Bad Request"
