import logging
from dataclasses import dataclass
from typing import Self, override

import pytest
from mpt_extension_sdk.models import Order, Product, Template
from mpt_extension_sdk.pipeline import OrderContext
from mpt_extension_sdk.services.api_client_v2.mpt_api_client import AsyncMPTClient
from mpt_extension_sdk.services.mpt_api_service.api_service import MPTAPIService
from mpt_extension_sdk.services.mpt_api_service.order import OrderService
from mpt_extension_sdk.services.mpt_api_service.template import TemplateService
from mpt_extension_sdk.settings.extension import BaseExtensionSettings


@dataclass(frozen=True)
class OrderStatusSettings(BaseExtensionSettings):
    @override
    @classmethod
    def load(cls) -> Self:
        return cls()


@pytest.fixture
def extension_settings():
    return OrderStatusSettings()


@pytest.fixture
def mpt_api_service(mocker):
    service = MPTAPIService(mocker.create_autospec(AsyncMPTClient, instance=True))
    service.orders = mocker.create_autospec(OrderService, instance=True)
    service.templates = mocker.create_autospec(TemplateService, instance=True)
    return service


@pytest.fixture
def template_factory():
    def factory(template_id="TPL-1", name="My template", *, default=False):
        return Template.model_construct(id=template_id, name=name, default=default)

    return factory


@pytest.fixture
def order_context_factory(
    mpt_api_service,
    extension_settings,
    runtime_settings,
    event_metadata,
    parameter_bag_factory,
):
    def factory(status="Processing", product_id="PRD-1", template=None):
        order = Order.model_construct(
            id="ORD-0001",
            status=status,
            product=Product.model_construct(id=product_id, name="Test product"),
            template=template,
            parameters=parameter_bag_factory(),
        )
        return OrderContext(
            logger=logging.getLogger("tests"),
            mpt_api_service=mpt_api_service,
            ext_settings=extension_settings,
            runtime_settings=runtime_settings,
            meta=event_metadata,
            order=order,
        )

    return factory
