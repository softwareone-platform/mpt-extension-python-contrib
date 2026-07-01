# Usage

`mpt-extension-contrib-fixtures` provides pytest fixtures and
[polyfactory](https://polyfactory.litestar.dev/) factories for MPT-shaped
objects (orders, agreements, subscriptions). Factories build **structurally
valid SDK models with empty parameters**; the product-specific parameter
catalog stays in the consumer.

## Install

```bash
pip install mpt-extension-contrib-fixtures
# or, with uv
uv add --dev mpt-extension-contrib-fixtures
```

The package registers a pytest plugin via the `pytest11` entry point, so its
fixtures are available as soon as it is installed — no `conftest.py` wiring.

## Fixtures provided by the plugin

| Fixture | Returns |
| --- | --- |
| `order_factory` | the `OrderFactory` class |
| `agreement_factory` | the `AgreementFactory` class |
| `subscription_factory` | the `SubscriptionFactory` class |
| `parameter_bag` | the `parameter_bag` helper |
| `mpt_error_factory` | the `mpt_error_factory` helper |

```python
def test_uses_plugin_fixtures(order_factory, parameter_bag):
    order = order_factory.purchase(parameters=parameter_bag(ordering={"accountType": "New"}))

    assert order.type == "Purchase"
```

For advanced use (subclassing factories, building scenarios), import from the
package root:

```python
from mpt_extension_contrib.fixtures import (
    AgreementFactory,
    OrderFactory,
    Scenarios,
    SubscriptionFactory,
    mpt_error_factory,
    parameter_bag,
)
```

## Building models

Each factory is a polyfactory `ModelFactory`. `build()` returns a fully valid
model; pass any field as a keyword to override it.

```python
order = OrderFactory.build()  # random-but-valid, empty parameters
order = OrderFactory.build(status="Querying")
agreement = AgreementFactory.build(name="ACME")
subscription = SubscriptionFactory.build()
```

Parameters default to an empty `ParameterBag` everywhere, including nested
models, so factory output never contains random parameter values.

### Order-type presets (the platform axis)

Order `type` is an MPT-platform concept, so presets ship with the library:

```python
OrderFactory.purchase()  # type="Purchase"
OrderFactory.change()  # type="Change"
OrderFactory.terminate()  # type="Termination"
OrderFactory.configuration()  # type="Configuration"
```

Each accepts the same field overrides as `build()`.

## Injecting parameters (the consumer axis)

Parameter values are product-specific (AWS uses `accountType`/`mpaId`, Adobe
uses `companyName`/3YC, …), so the **catalog belongs to the consumer**. The
library only provides the shape and the injection seams.

### `parameter_bag` helper

Turn a flat `{external_id: value}` catalog into a `ParameterBag`:

```python
bag = parameter_bag(
    ordering={"accountType": "New", "mpaId": "123456"},
    fulfillment={"phase": "precondition"},
)
order = OrderFactory.purchase(parameters=bag)
```

### Per-test override

```python
order = OrderFactory.purchase(parameters=parameter_bag(ordering={"accountType": "Migrate"}))
```

### Reusable consumer factory subclass

Keep your catalog in your own test code and overlay it once:

```python
from polyfactory import Use
from mpt_extension_contrib.fixtures import OrderFactory, parameter_bag


class AwsOrderFactory(OrderFactory):
    parameters = Use(lambda: parameter_bag(ordering={"accountType": "New", "mpaId": "123456"}))


order = AwsOrderFactory.build()  # always carries the AWS catalog
order = AwsOrderFactory.build(status="Querying")  # structure still overridable
```

## Predefined scenarios (not random)

When a state implies a specific set of parameters (e.g. an AWS *migration* order
is a `Purchase` with a particular catalog), encode it explicitly rather than
relying on random data.

### Named preset constructors

```python
class AwsOrderFactory(OrderFactory):
    @classmethod
    def migration(cls, **overrides):
        return cls.purchase(
            parameters=parameter_bag(ordering={"accountType": "Migrate", "mpaId": "123456"}),
            **overrides,
        )


order = AwsOrderFactory.migration()
order = AwsOrderFactory.migration(status="Processing")
```

### Deriving parameters from status

When one factory should "know" the status-to-parameters rule, compute the
parameters from the already-generated fields with polyfactory's
`PostGenerated`:

```python
from polyfactory import PostGenerated
from mpt_extension_contrib.fixtures import parameter_bag


def _aws_params(_name, values, *_):
    rules = {
        "Processing": parameter_bag(fulfillment={"phase": "precondition"}),
        "Querying": parameter_bag(ordering={"accountType": "New"}),
    }
    return rules.get(values["status"], parameter_bag())


class AwsOrderFactory(OrderFactory):
    parameters = PostGenerated(_aws_params)


AwsOrderFactory.build(status="Processing")  # parameters filled per the rule
```

## Named scenarios (`Scenarios`)

A `Scenarios` binds a factory to a registry of named specs. A spec is just a dict
of **factory field overrides** passed straight to `build` — so a scenario can vary
anything the model has: `status`, `type`, `lines`, `subscriptions`, `template`,
and `parameters` (parameters are one field among many, not a special case). The
same type works for any entity, so there is no per-entity helper.

```python
from mpt_extension_contrib.fixtures import OrderFactory, Scenarios, parameter_bag

ORDERS = Scenarios(
    OrderFactory,
    {
        "new_purchase": {"type": "Purchase", "status": "Processing"},
        "querying": {"type": "Purchase", "status": "Querying"},
        "change": {"type": "Change", "lines": [...]},
        # parameters are just another field:
        "with_params": {
            "type": "Purchase",
            "parameters": parameter_bag(ordering={"accountType": "New"}),
        },
    },
)

# Build one scenario by name (extra kwargs are field overrides):
order = ORDERS.build("change", status="Processing")
```

The same shape works for any factory, e.g. `AGREEMENTS = Scenarios(AgreementFactory, {...})`.

### Run a test for each scenario

`Scenarios.fixture()` returns a parametrized fixture; any test that requests it
runs once per scenario, with the registry key as the test id:

```python
# conftest.py
order = ORDERS.fixture()


# test_orders.py
def test_fulfillment(order):  # runs once per scenario
    assert run_flow(order).ok
```

Or parametrize explicitly with `Scenarios.cases()` (built models, optional subset):

```python
@pytest.mark.parametrize("order", ORDERS.cases())
def test_flow(order): ...


@pytest.mark.parametrize("order", ORDERS.cases(only=["querying", "change"]))
def test_subset(order): ...
```

### Schema-driven variety

For coverage of every schema variant (rather than your curated cases), use
polyfactory directly:

```python
OrderFactory.batch(5)  # five random-but-valid orders
list(OrderFactory.coverage())  # minimal set covering enum/union/optional variants
```

## Mocking the MPT API (at the SDK layer)

Factories build typed SDK models (`mpt_extension_sdk.models`). The SDK wraps every
API response into those models via `from_payload`, so mock at the SDK service layer
and return a factory model directly — it matches what production code receives:

```python
mocker.patch.object(order_service, "get_by_id", return_value=OrderFactory.purchase())
```

`.to_dict()` serialises a model to the exact camelCase JSON the API returns
(useful when a test needs the raw payload):

```python
payload = OrderFactory.purchase().to_dict()  # API-shaped dict
```

> HTTP/wire-level mocking (httpx/`respx`) and response-envelope helpers
> (`api_object`, `api_collection`, `api_error`) are **not** part of this module for
> now — mock at the SDK layer. See [architecture.md](architecture.md) for the
> SDK-vs-client boundary and the roadmap.

## MPT error payloads

`mpt_error_factory` builds an MPT API error payload (a plain dict, not a model):

```python
error = mpt_error_factory(400, "Bad Request", "Invalid order")
error = mpt_error_factory(400, "Bad Request", "x", field_errors={"name": ["required"]})
```
