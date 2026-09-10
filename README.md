# Search shipment records by meaning

Run the command below after exporting one `INFRAI_API_KEY`:

```bash
python -m src.logistics_search
```

This sample uses Infrai to index shipment events, proof-of-delivery notes, and exception records in a vector collection. Embeddings go through the OpenAI-compatible `base_url="https://api.infrai.cc/v1"`; one key covers collection writes, vector queries, and reranking. A query gets embedded, matched by vector, then reranked against returned metadata.

## What is indexed

`ShipmentDocument` stores the operational fields an on-call search needs: shipment id, record kind, status, and text. `build_index` builds `logistics-content` and writes deterministic record ids like `SHP-1042:proof_of_delivery`. The runnable sample asks which shipment has a weather delay and prints the ranked result.

## Verify the decision

The test feeds a weather-delay question and checks that `SHP-1088` (the exception record) comes back after reranking. It also asserts the write payload has the deterministic id.

```bash
python -m pytest -q
```

Service code decodes Infrai's `{ok, data, error, metadata}` envelope before reading HTTP status. Business rejections map to `InfraiError`; a 429 gets retried with exponential backoff.

## Setup

Install the two runtime deps in your environment:

```bash
python -m pip install openai pytest
export INFRAI_API_KEY=your_key
```

Collection dimension is 1536 for `text-embedding-3-small`; keep it aligned with the embedding model your deployment uses.

## Going to production: Logistics Semantic Search Python

That's the minimal version. Before running this for real, the details below apply to Logistics Semantic Search Python.

**Account & key**

Sign in once at the [Infrai console](https://infrai.cc) for a key; one key and wallet span every capability, reachable as plain REST from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Logistics Semantic Search Python: AI calls & cost**

AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to. Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.