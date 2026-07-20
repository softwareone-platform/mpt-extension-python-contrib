import logging
from pathlib import Path

import pytest
from mpt_extension_sdk.models import Order, ParameterBag
from mpt_extension_sdk.pipeline import EventMetadata, OrderContext
from mpt_extension_sdk.runtime.models import MetaConfig
from mpt_extension_sdk.services.api_client_v2.mpt_api_client import AsyncMPTClient
from mpt_extension_sdk.services.mpt_api_service.api_service import MPTAPIService
from mpt_extension_sdk.services.mpt_api_service.order import OrderService
from mpt_extension_sdk.settings.runtime import RuntimeSettings


@pytest.fixture
def parameter_bag_factory():
    def factory(ordering=None, fulfillment=None):
        return ParameterBag(ordering=ordering or [], fulfillment=fulfillment or [])

    return factory


@pytest.fixture
def event_metadata():
    return EventMetadata(
        event_id="evt-1",
        object_id="ORD-0001",
        object_type="order",
        task_id="task-1",
    )


@pytest.fixture
def runtime_settings():
    return RuntimeSettings(
        app_module="extension.app",
        settings_module="extension.settings",
        ext_api_key="test-key",
        base_url="https://sdk.test",
        extension_id="EXT-0001",
        mpt_api_base_url="https://mpt.test",
        external_id="extension-local",
        identity_file_path=Path("/tmp/identity.json"),
        meta_config=MetaConfig(openapi="/openapi.json", events=[]),
        meta_file_path=Path("meta.yaml"),
        local_host="127.0.0.1",
        local_port=8080,
        local_reload=False,
        local_workers=1,
        log_level="INFO",
        observability_enabled=False,
        applicationinsights_connection_string="",
        otel_service_name="",
        otel_otlp_endpoint="",
        ziti_workers=1,
        ziti_reload=False,
    )


@pytest.fixture
def mpt_api_service(mocker):
    service = MPTAPIService(mocker.create_autospec(AsyncMPTClient, instance=True))
    service.orders = mocker.create_autospec(OrderService, instance=True)
    return service


@pytest.fixture
def order_context_factory(
    parameter_bag_factory,
    mpt_api_service,
    extension_settings,
    runtime_settings,
    event_metadata,
):
    def factory(ordering=None, fulfillment=None):
        order = Order.model_construct(
            id="ORD-0001",
            parameters=parameter_bag_factory(ordering=ordering, fulfillment=fulfillment),
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
