import pytest


def test_plugin_registers_fixtures(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        """
        def test_order_factory(order_factory):
            assert order_factory.purchase().type == "Purchase"

        def test_agreement_factory(agreement_factory):
            assert agreement_factory.build().name

        def test_subscription_factory(subscription_factory):
            assert subscription_factory.build().id

        def test_parameter_bag(parameter_bag):
            bag = parameter_bag(ordering={"accountType": "New"})
            assert bag.get_ordering_value("accountType") == "New"

        def test_mpt_error_factory(mpt_error_factory):
            assert mpt_error_factory(404, "Not Found", "missing")["status"] == 404
        """,
    )

    result = pytester.runpytest_subprocess()

    result.assert_outcomes(passed=5)
