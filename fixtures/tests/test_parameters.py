from mpt_extension_contrib.fixtures import parameter_bag


def test_parameter_bag_builds_ordering() -> None:
    result = parameter_bag(ordering={"accountType": "New", "mpaId": "123"})

    assert result.get_ordering_value("accountType") == "New"
    assert result.get_ordering_value("mpaId") == "123"


def test_parameter_bag_builds_fulfillment() -> None:
    result = parameter_bag(fulfillment={"phase": "precondition"})

    assert result.get_fulfillment_value("phase") == "precondition"


def test_parameter_bag_defaults_to_empty() -> None:
    result = parameter_bag()

    assert result.ordering == []
    assert result.fulfillment == []
