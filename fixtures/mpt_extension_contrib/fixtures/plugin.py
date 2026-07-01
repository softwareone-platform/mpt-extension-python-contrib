"""Pytest plugin exposing MPT factories and helpers as fixtures.

Registered through the ``pytest11`` entry point, so installing the package
makes these fixtures available without importing anything in ``conftest.py``.

The plugin module loads during pytest startup, before coverage instrumentation
begins. Implementation modules are therefore resolved lazily (via
``importlib``) inside each fixture, so their code stays measurable by the test
suite instead of being imported once, uncovered, at startup.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

import pytest

if TYPE_CHECKING:
    from mpt_extension_contrib.fixtures.factories import (
        AgreementFactory,
        OrderFactory,
        SubscriptionFactory,
    )

_FACTORIES = "mpt_extension_contrib.fixtures.factories"
_BAG_MODULE = "mpt_extension_contrib.fixtures.parameters"
_ERRORS = "mpt_extension_contrib.fixtures.errors"


@pytest.fixture
def order_factory() -> type[OrderFactory]:
    """Return the order factory class for ``build`` or subclassing."""
    module = importlib.import_module(_FACTORIES)
    return cast("type[OrderFactory]", module.OrderFactory)


@pytest.fixture
def agreement_factory() -> type[AgreementFactory]:
    """Return the agreement factory class for ``build`` or subclassing."""
    module = importlib.import_module(_FACTORIES)
    return cast("type[AgreementFactory]", module.AgreementFactory)


@pytest.fixture
def subscription_factory() -> type[SubscriptionFactory]:
    """Return the subscription factory class for ``build`` or subclassing."""
    module = importlib.import_module(_FACTORIES)
    return cast("type[SubscriptionFactory]", module.SubscriptionFactory)


@pytest.fixture
def parameter_bag() -> Callable[..., Any]:
    """Return the parameter-bag builder helper."""
    module = importlib.import_module(_BAG_MODULE)
    return cast("Callable[..., Any]", module.parameter_bag)


@pytest.fixture
def mpt_error_factory() -> Callable[..., Any]:
    """Return the MPT API error payload factory."""
    module = importlib.import_module(_ERRORS)
    return cast("Callable[..., Any]", module.mpt_error_factory)
