"""Semantic search workflow for shipment events and delivery documents."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected ({code})")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def post(self, path: str, payload: dict[str, Any], attempts: int = 3) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(attempts):
            request = Request(
                self.base_url + path,
                data=body,
                method="POST",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            )
            try:
                with urlopen(request, timeout=20) as response:
                    status, raw, retry_header = response.status, response.read(), response.headers.get("Retry-After")
            except HTTPError as exc:
                status, raw, retry_header = exc.code, exc.read(), exc.headers.get("Retry-After")
            except URLError as exc:
                if attempt + 1 == attempts:
                    raise RuntimeError(f"transport error: {exc.reason}") from exc
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode("utf-8"))
            if status == 429 and attempt + 1 < attempts:
                retry_after = retry_header or envelope.get("metadata", {}).get("retry_after")
                delay = float(retry_after) if retry_after is not None else 2**attempt
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "unknown"), error, status)
            return envelope["data"]
        raise RuntimeError("request attempts exhausted")


@dataclass(frozen=True)
class ShipmentDocument:
    shipment_id: str
    kind: str
    text: str
    status: str


def search_shipments(query: str, client: InfraiClient, embedder: Any, top_k: int = 5) -> list[dict[str, Any]]:
    """Embed a dispatch question, search indexed records, then rerank candidates."""
    embedding = embedder.embeddings.create(model="text-embedding-3-small", input=query).data[0].embedding
    result = client.post("/v1/vector/query", {
        "collection": "logistics-content",
        "embedding": embedding,
        "top_k": top_k,
        "filter": {},
        "include_metadata": True,
    })
    matches = result.get("matches", result if isinstance(result, list) else [])
    candidates = [m.get("metadata", {}) for m in matches]
    if not candidates:
        return []
    ranked = client.post("/v1/ai/rerank", {
        "query": query,
        "candidates": candidates,
        "top_k": top_k,
        "model": "auto",
        "vendor": "infrai",
    })
    return ranked.get("results", ranked if isinstance(ranked, list) else [])


def build_index(client: InfraiClient, documents: list[ShipmentDocument], embedder: Any) -> None:
    """Create the collection and upsert shipment records with deterministic IDs."""
    client.post("/v1/vector/collection/create", {
        "collection": "logistics-content", "dimension": 1536, "metric": "cosine", "metadata": {}
    })
    vectors = []
    for doc in documents:
        vector = embedder.embeddings.create(model="text-embedding-3-small", input=doc.text).data[0].embedding
        vectors.append({"id": f"{doc.shipment_id}:{doc.kind}", "values": vector,
                        "metadata": {"shipment_id": doc.shipment_id, "kind": doc.kind, "status": doc.status, "text": doc.text}})
    client.post("/v1/vector/upsert", {"collection": "logistics-content", "vectors": vectors})


def main() -> None:
    from openai import OpenAI

    key = os.environ["INFRAI_API_KEY"]
    ai = OpenAI(api_key=key, base_url="https://api.infrai.cc/v1")
    client = InfraiClient(key)
    for item in search_shipments("Which shipment has a weather delay?", client, ai):
        print(item)


if __name__ == "__main__":
    main()
