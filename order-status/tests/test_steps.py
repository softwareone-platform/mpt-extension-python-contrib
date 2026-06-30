import pytest
from mpt_extension_contrib.order_status import CompleteOrder, StartOrderProcessing
from mpt_extension_sdk.errors.step import SkipStepError, StopStepError


async def test_complete_order_completes_with_template(order_context_factory, template_factory):
    context = order_context_factory(status="Processing")
    context.mpt_api_service.templates.get_template.return_value = template_factory(name="Completed")
    orders = context.mpt_api_service.orders

    await CompleteOrder().run(context)

    orders.complete.assert_awaited_once()


async def test_complete_order_refreshes_order(order_context_factory, template_factory):
    context = order_context_factory(status="Processing")
    context.mpt_api_service.templates.get_template.return_value = template_factory(name="Completed")
    orders = context.mpt_api_service.orders

    await CompleteOrder().run(context)

    orders.get_by_id.assert_awaited_once()


async def test_complete_order_skips_if_completed(order_context_factory):
    context = order_context_factory(status="Completed")
    orders = context.mpt_api_service.orders

    with pytest.raises(SkipStepError):
        await CompleteOrder().run(context)

    orders.complete.assert_not_awaited()


async def test_complete_order_stops_when_no_template(order_context_factory):
    context = order_context_factory(status="Processing")
    context.mpt_api_service.templates.get_template.return_value = None

    with pytest.raises(StopStepError):
        await CompleteOrder().run(context)


async def test_start_processing_sets_when_unset(order_context_factory, template_factory):
    context = order_context_factory(template=None)
    new_template = template_factory(template_id="NEW")
    context.mpt_api_service.templates.get_template.return_value = new_template
    templates = context.mpt_api_service.templates

    await StartOrderProcessing().run(context)

    templates.set_order_template.assert_awaited_once_with("ORD-0001", new_template)


async def test_start_processing_sets_when_changed(order_context_factory, template_factory):
    context = order_context_factory(template=template_factory(template_id="OLD"))
    context.mpt_api_service.templates.get_template.return_value = template_factory(
        template_id="NEW"
    )
    orders = context.mpt_api_service.orders

    await StartOrderProcessing().run(context)

    orders.get_by_id.assert_awaited_once()


async def test_start_processing_skips_when_unchanged(order_context_factory, template_factory):
    context = order_context_factory(template=template_factory(template_id="SAME"))
    context.mpt_api_service.templates.get_template.return_value = template_factory(
        template_id="SAME"
    )
    templates = context.mpt_api_service.templates

    await StartOrderProcessing().run(context)

    templates.set_order_template.assert_not_awaited()


async def test_start_processing_no_template(order_context_factory):
    context = order_context_factory(template=None)
    context.mpt_api_service.templates.get_template.return_value = None
    templates = context.mpt_api_service.templates

    await StartOrderProcessing().run(context)

    templates.set_order_template.assert_not_awaited()
