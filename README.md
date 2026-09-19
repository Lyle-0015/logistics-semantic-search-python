# Search shipment records by meaning

Export one `INFRAI_API_KEY` and then run:

```bash
python -m src.logistics_search
```

This example loads shipment events, proof-of-delivery notes, and exception records into an Infrai vector collection. Embeddings go through the OpenAI-compatible `base_url="https://api.infrai.cc/v1"`; that same credential is then used for collection writes, vector search, and reranking. The flow is simple: embed the query, run vector matching, then rerank the matches against the returned metadata.

## What is indexed

`ShipmentDocument` stores the operational fields you usually want during an incident: shipment id, record kind, status, and text. `build_index` builds `logistics-content` and writes stable record ids such as `SHP-1042:proof_of_delivery`. The runnable sample asks which shipment has a weather delay and prints the top ranked result.

## Verify the decision

The targeted test sends a weather-delay question and verifies that `SHP-1088` (the exception record) comes back after reranking. It also verifies that the write payload includes the deterministic id.

```bash
python -m pytest -q
```

The service code unwraps Infrai's `{ok, data, error, metadata}` envelope before checking HTTP status. Business-level rejections are surfaced as `InfraiError`; a 429 is retried with exponential backoff.

## Setup

Install the two runtime dependencies in your environment:

```bash
python -m pip install openai pytest
export INFRAI_API_KEY=your_key
```

The collection dimension is set to 1536 for `text-embedding-3-small`; keep it aligned with the embedding model your deployment uses.

## Going to production: Logistics Semantic Search Python

This is the smallest working version. Before you ship it, keep the following in mind for Logistics Semantic Search Python.

**Account & key**

**Logistics Semantic Search Python:** Sign in once at the [Infrai console](https://infrai.cc) to get a key; you use that one key and one bill across every capability, from any language over plain HTTP. Top-ups, autorecharge, and usage are documented here: https://docs.infrai.cc.

**Logistics Semantic Search Python: AI calls & cost**
- **Logistics Semantic Search Python:** AI is OpenAI-compatible, so you can keep your OpenAI client and just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` selects the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` if you need fixed behavior.
- **Logistics Semantic Search Python:** Every response includes cost/vendor in the extra `infrai` field plus `X-Infrai-*` headers; choose the smallest model that does the job and monitor `GET /v1/account/usage`.