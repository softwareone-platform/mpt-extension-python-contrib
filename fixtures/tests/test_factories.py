from mpt_extension_contrib.fixtures import OrderFactory, parameter_bag


def test_build_has_empty_parameters() -> None:
    result = OrderFactory.build()

    assert result.parameters.ordering == []
    assert result.parameters.fulfillment == []


def test_nested_agreement_params_empty() -> None:
    result = OrderFactory.build()

    assert result.agreement.parameters.ordering == []


def test_purchase_preset_sets_type() -> None:
    result = OrderFactory.purchase()

    assert result.type == "Purchase"


def test_change_preset_sets_type() -> None:
    result = OrderFactory.change()

    assert result.type == "Change"


def test_terminate_preset_sets_type() -> None:
    result = OrderFactory.terminate()

    assert result.type == "Termination"


def test_configuration_preset_sets_type() -> None:
    result = OrderFactory.configuration()

    assert result.type == "Configuration"


def test_build_accepts_parameter_override() -> None:
    bag = parameter_bag(ordering={"accountType": "New"})

    result = OrderFactory.purchase(parameters=bag)

    assert result.type == "Purchase"
    assert result.parameters.get_ordering_value("accountType") == "New"
