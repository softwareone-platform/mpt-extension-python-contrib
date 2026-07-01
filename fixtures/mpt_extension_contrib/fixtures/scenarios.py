"""Named scenario sets for building MPT models and driving pytest parametrization.

A ``Scenarios`` binds a factory to a registry of named specs. A spec is just a
dict of factory field overrides, passed straight to ``build`` — so a scenario can
vary anything the model has (status, type, lines, subscriptions, template,
parameters, ...). It works for any model factory, so there is no per-entity helper.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import pytest
from mpt_extension_sdk.models.base import BaseModel
from polyfactory.factories.pydantic_factory import ModelFactory

Spec = dict[str, Any]


class Scenarios[ModelT: BaseModel]:
    """A named set of model specs bound to a factory.

    Build a single model by name with :meth:`build`, or fan the whole set out
    over pytest with :meth:`cases` (explicit ``parametrize``) or :meth:`fixture`
    (a ready parametrized fixture). The registry key is used as the test id.
    """

    def __init__(
        self,
        factory: type[ModelFactory[ModelT]],
        registry: Mapping[str, Spec],
    ) -> None:
        self._factory = factory
        self._registry = dict(registry)

    def build(self, name: str, **overrides: Any) -> ModelT:
        """Build the named scenario, applying any extra field overrides.

        The spec and ``overrides`` are passed to the factory as field values, so
        a scenario can set any model field (``status``, ``type``, ``lines``,
        ``subscriptions``, ``template``, ``parameters``, ...).
        """
        return self._factory.build(**{**self._registry[name], **overrides})

    def cases(self, only: Iterable[str] | None = None) -> list[Any]:
        """Return built models as ``pytest.param`` cases for ``parametrize``.

        Pass ``only`` to select a subset of scenario names.
        """
        names = list(self._registry) if only is None else list(only)
        return [pytest.param(self.build(name), id=name) for name in names]

    def fixture(self) -> Any:
        """Return a parametrized pytest fixture yielding each scenario in turn.

        Wire it once in a ``conftest.py`` (``order = ORDERS.fixture()``); any
        test requesting the fixture then runs once per registry entry.
        """

        @pytest.fixture(params=list(self._registry), ids=list(self._registry))
        def factory(request: pytest.FixtureRequest) -> ModelT:
            return self.build(request.param)

        return factory
