import logging

from mpt_extension_contrib.order_status import OrderStatus, resolve_template


async def test_resolve_returns_named_template(mpt_api_service, template_factory):
    named = template_factory(template_id="TPL-1", name="Custom", default=False)
    mpt_api_service.templates.get_template.return_value = named

    result = await resolve_template(
        mpt_api_service, product_id="PRD-1", status=OrderStatus.COMPLETED, template_name="Custom"
    )

    assert result is named
    mpt_api_service.templates.get_template.assert_awaited_once_with(
        "PRD-1", "Completed", name="Custom"
    )


async def test_resolve_logs_fallback_to_default(mpt_api_service, template_factory, caplog):
    caplog.set_level(logging.INFO)
    default = template_factory(template_id="TPL-DEF", name="Default", default=True)
    mpt_api_service.templates.get_template.return_value = default

    result = await resolve_template(
        mpt_api_service, product_id="PRD-1", status=OrderStatus.COMPLETED, template_name="Missing"
    )

    assert result is default
    assert "not found" in caplog.text


async def test_resolve_logs_when_no_template_found(mpt_api_service, caplog):
    caplog.set_level(logging.INFO)
    mpt_api_service.templates.get_template.return_value = None

    result = await resolve_template(
        mpt_api_service, product_id="PRD-1", status=OrderStatus.COMPLETED, template_name="Missing"
    )

    assert result is None
    assert "not found" in caplog.text


async def test_resolve_default_request_does_not_log(mpt_api_service, template_factory, caplog):
    caplog.set_level(logging.INFO)
    default = template_factory(name="Default", default=True)
    mpt_api_service.templates.get_template.return_value = default

    result = await resolve_template(
        mpt_api_service, product_id="PRD-1", status=OrderStatus.COMPLETED
    )

    assert result is default
    assert "not found" not in caplog.text
