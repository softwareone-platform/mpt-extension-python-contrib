"""Polyfactory factories for MPT SDK models.

Factories build structurally valid SDK models with empty parameter bags by
default. Product-specific parameters belong to the consumer and are injected at
build time; see ``docs/usage.md`` for the supported injection seams.
"""

from __future__ import annotations

from typing import Any, TypeVar

from mpt_extension_sdk.models import Agreement, Order, ParameterBag, Subscription
from mpt_extension_sdk.models.base import BaseModel
from polyfactory import Use
from polyfactory.factories.pydantic_factory import ModelFactory

ModelT = TypeVar("ModelT", bound=BaseModel)


class ParameterBagFactory(ModelFactory[ParameterBag]):
    """Build an empty parameter bag everywhere a ``ParameterBag`` is needed.

    Registered as the default factory for its type so nested models (agreement,
    subscription, order) never receive randomly generated parameters.
    """

    __set_as_default_factory_for_type__ = True
    __check_model__ = False

    ordering: Any = Use(list)  # noqa: WPS110 - field name mirrors the SDK model
    fulfillment: Any = Use(list)


class MPTModelFactory(ModelFactory[ModelT]):
    """Base factory that keeps SDK model defaults.

    With defaults honoured, optional collections (lines, assets, subscriptions)
    and parameter bags stay empty; only required fields are generated.
    """

    __is_base_factory__ = True
    __use_defaults__ = True
    __check_model__ = False


class AgreementFactory(MPTModelFactory[Agreement]):
    """Build a structurally valid MPT agreement with empty parameters."""


class SubscriptionFactory(MPTModelFactory[Subscription]):
    """Build a structurally valid MPT subscription with empty parameters."""


class OrderFactory(MPTModelFactory[Order]):
    """Build a structurally valid MPT order with empty parameters.

    Order-type presets cover the platform axis (purchase, change, termination,
    configuration). The consumer overlays the product parameter catalog through
    the ``parameters`` build override.
    """

    # TODO: replace the literal order types (and statuses passed by consumers)
    # with canonical StrEnums once they land in mpt-extension-sdk, where
    # ``Order.type`` / ``Order.status`` still carry their own "add enum" TODO.
    # Defining those domain enums in this test library would add a copy that
    # production code must not import, so they belong in the SDK, not here.

    @classmethod
    def purchase(cls, **overrides: Any) -> Order:
        """Build a purchase order."""
        return cls.build(type="Purchase", **overrides)

    @classmethod
    def change(cls, **overrides: Any) -> Order:
        """Build a change order."""
        return cls.build(type="Change", **overrides)

    @classmethod
    def terminate(cls, **overrides: Any) -> Order:
        """Build a termination order."""
        return cls.build(type="Termination", **overrides)

    @classmethod
    def configuration(cls, **overrides: Any) -> Order:
        """Build a configuration order."""
        return cls.build(type="Configuration", **overrides)
