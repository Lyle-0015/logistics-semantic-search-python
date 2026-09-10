from types import SimpleNamespace

from src.logistics_search import InfraiClient, ShipmentDocument, build_index, search_shipments


class FakeEmbeddings:
    def create(self, **kwargs):
        return SimpleNamespace(data=[SimpleNamespace(embedding=[0.1, 0.2, 0.3])])


class FakeAI:
    embeddings = FakeEmbeddings()


class FakeClient(InfraiClient):
    def __init__(self):
        super().__init__("test")
        self.calls = []

    def post(self, path, payload, attempts=3):
        self.calls.append((path, payload))
        if path.endswith("query"):
            return {"matches": [{"metadata": {"shipment_id": "SHP-1088", "status": "exception"}}]}
        if path.endswith("rerank"):
            return {"results": [{"shipment_id": "SHP-1088", "status": "exception"}]}
        return {}


def test_exception_search_returns_ranked_shipment():
    client = FakeClient()
    result = search_shipments("weather delay", client, FakeAI())
    assert result == [{"shipment_id": "SHP-1088", "status": "exception"}]
    assert client.calls[0][0] == "/v1/vector/query"


def test_index_writes_each_document():
    client = FakeClient()
    build_index(client, [ShipmentDocument("S1", "event", "arrived", "in_transit")], FakeAI())
    assert client.calls[-1][0] == "/v1/vector/upsert"
    assert client.calls[-1][1]["vectors"][0]["id"] == "S1:event"
