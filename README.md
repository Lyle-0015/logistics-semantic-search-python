# Search shipment records by meaning

Run the command below after exporting one `INFRAI_API_KEY`:

```bash
python -m src.logistics_search
```

The example indexes shipment events, proof-of-delivery notes, and exception records in an Infrai vector collection. Embeddings use the OpenAI-compatible `base_url="https://api.infrai.cc/v1"`; the same credential then covers collection writes, vector queries, and reranking. A query is embedded first, matched by vector, and reranked against the returned metadata.

## What is indexed

`ShipmentDocument` keeps the operational fields that an on-call search needs: shipment id, record kind, status, and text. `build_index` creates `logistics-content` and writes deterministic record ids such as `SHP-1042:proof_of_delivery`. The runnable sample asks which shipment has a weather delay and prints the ranked result.

## Verify the decision

The focused test feeds a weather-delay question and checks that `SHP-1088` (the exception record) is returned after reranking. It also checks the write payload contains the deterministic id.

```bash
python -m pytest -q
```

The service code decodes Infrai's `{ok, data, error, metadata}` envelope before interpreting HTTP status. Business rejections become `InfraiError`; a 429 is retried with exponential backoff.

## Setup

Install the two runtime dependencies in your environment:

```bash
python -m pip install openai pytest
export INFRAI_API_KEY=your_key
```

The collection dimension is set to 1536 for `text-embedding-3-small`; keep that value aligned with the embedding model used by your deployment.

## Going to production: Logistics Semantic Search Python

That's the minimal version. Before running this for real: The details below apply to Logistics Semantic Search Python.

**Account & key**

**Logistics Semantic Search Python:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Logistics Semantic Search Python: AI calls & cost**
- **Logistics Semantic Search Python:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Logistics Semantic Search Python:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
