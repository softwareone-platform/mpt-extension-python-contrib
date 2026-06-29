from mpt_api_client.rql import RQLQuery
from mpt_extension_contrib.reports import AsyncReportCreator, ReportCreator


class FakeResource:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return self._payload


class FakeService:
    def __init__(self, payloads):
        self._payloads = payloads
        self.applied_query = None
        self.applied_select = None
        self.batch_size = None

    def filter(self, rql):
        self.applied_query = rql
        return self

    def select(self, *fields):
        self.applied_select = fields
        return self

    def iterate(self, batch_size=100):
        self.batch_size = batch_size
        return iter([FakeResource(payload) for payload in self._payloads])


class FakeAsyncService:
    def __init__(self, payloads):
        self._payloads = payloads
        self.applied_select = None
        self.batch_size = None

    def filter(self, rql):
        return self

    def select(self, *fields):
        self.applied_select = fields
        return self

    async def iterate(self, batch_size=100):
        self.batch_size = batch_size
        for payload in self._payloads:
            yield FakeResource(payload)


def _id_status_mapper(resource):
    return [resource["id"], resource["status"]]


def test_create_applies_query_and_select():
    service = FakeService([
        {"id": "ORD-1", "status": "Querying"},
        {"id": "ORD-2", "status": "Processing"},
    ])
    query = RQLQuery(status__in=["Querying", "Processing"])
    creator = ReportCreator(
        service,
        _id_status_mapper,
        query=query,
        select=["audit", "parameters"],
        batch_size=50,
    )

    result = creator.create()

    assert result.rows == [["ORD-1", "Querying"], ["ORD-2", "Processing"]]
    assert service.applied_query is query
    assert service.applied_select == ("audit", "parameters")
    assert service.batch_size == 50


def test_create_uses_defaults():
    service = FakeService([{"id": "ORD-1", "status": "Querying"}])
    creator = ReportCreator(service, _id_status_mapper)

    result = creator.create()

    assert result.rows == [["ORD-1", "Querying"]]
    assert service.applied_query is None
    assert service.applied_select is None
    assert service.batch_size == 100


def test_create_treats_empty_select_as_unset():
    service = FakeService([{"id": "ORD-1", "status": "Querying"}])
    creator = ReportCreator(service, _id_status_mapper, select=[])

    result = creator.create()

    assert result.rows == [["ORD-1", "Querying"]]
    assert service.applied_select is None


def test_create_infers_headers_and_values():
    service = FakeService([{"id": "ORD-1", "lines": 3, "note": None}])
    creator = ReportCreator(service)

    result = creator.create()

    assert result.headers == ["id", "lines", "note"]
    assert result.rows == [["ORD-1", "3", ""]]


def test_create_flattens_nested_dicts():
    service = FakeService([{"id": "ORD-1", "client": {"id": "C1", "name": "Acme"}}])
    creator = ReportCreator(service)

    result = creator.create()

    assert result.headers == ["id", "client.id", "client.name"]
    assert result.rows == [["ORD-1", "C1", "Acme"]]


def test_create_infers_headers_from_first_payload():
    service = FakeService([
        {"id": "A", "status": "Querying"},
        {"id": "B", "status": "Processing"},
    ])
    creator = ReportCreator(service)

    result = creator.create()

    assert result.headers == ["id", "status"]
    assert result.rows == [["A", "Querying"], ["B", "Processing"]]


def test_create_infers_empty_report():
    creator = ReportCreator(FakeService([]))

    result = creator.create()

    assert result.headers == []
    assert result.rows == []


async def test_async_create_applies_query_and_select():
    service = FakeAsyncService([
        {"id": "ORD-1", "status": "Querying"},
        {"id": "ORD-2", "status": "Processing"},
    ])
    creator = AsyncReportCreator(service, _id_status_mapper, select=["audit"], batch_size=50)

    result = await creator.create()

    assert result.rows == [["ORD-1", "Querying"], ["ORD-2", "Processing"]]
    assert service.applied_select == ("audit",)
    assert service.batch_size == 50


async def test_async_create_infers_and_flattens():
    service = FakeAsyncService([{"id": "ORD-1", "client": {"id": "C1"}}])
    creator = AsyncReportCreator(service)

    result = await creator.create()

    assert result.headers == ["id", "client.id"]
    assert result.rows == [["ORD-1", "C1"]]
