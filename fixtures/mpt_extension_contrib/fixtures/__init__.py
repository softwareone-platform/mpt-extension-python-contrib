"""MPT pytest fixtures and polyfactory model factories.

Public API for building MPT-shaped test objects. The factories produce
structurally valid SDK models with empty parameters; product-specific parameter
catalogs and scenarios are supplied by the consumer. The pytest plugin
(registered via the ``pytest11`` entry point) also exposes these as ready-to-use
fixtures, with no ``conftest.py`` wiring required.

Names are resolved lazily (PEP 562): this package is imported during pytest
startup when the plugin registers, so eagerly importing the implementation here
would run its code before coverage instrumentation starts.
"""

from __future__ import annotations

import importlib
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mpt_extension_contrib.fixtures.errors import mpt_error_factory
    from mpt_extension_contrib.fixtures.factories import (
        AgreementFactory,
        MPTModelFactory,
        OrderFactory,
        ParameterBagFactory,
        SubscriptionFactory,
    )
    from mpt_extension_contrib.fixtures.parameters import parameter_bag
    from mpt_extension_contrib.fixtures.scenarios import Scenarios, Spec

__all__ = [
    "AgreementFactory",
    "MPTModelFactory",
    "OrderFactory",
    "ParameterBagFactory",
    "Scenarios",
    "Spec",
    "SubscriptionFactory",
    "mpt_error_factory",
    "parameter_bag",
]

_EXPORTS = MappingProxyType(
    {
        "AgreementFactory": "mpt_extension_contrib.fixtures.factories",
        "MPTModelFactory": "mpt_extension_contrib.fixtures.factories",
        "OrderFactory": "mpt_extension_contrib.fixtures.factories",
        "ParameterBagFactory": "mpt_extension_contrib.fixtures.factories",
        "SubscriptionFactory": "mpt_extension_contrib.fixtures.factories",
        "Scenarios": "mpt_extension_contrib.fixtures.scenarios",
        "Spec": "mpt_extension_contrib.fixtures.scenarios",
        "parameter_bag": "mpt_extension_contrib.fixtures.parameters",
        "mpt_error_factory": "mpt_extension_contrib.fixtures.errors",
    },
)


def __getattr__(name: str) -> Any:
    """Resolve a public name to its implementation module on first access."""
    module_path = _EXPORTS.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(importlib.import_module(module_path), name)
