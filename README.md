# AI Chatbot

A FastAPI chatbot built on LangChain and Claude, with long-term memory backed by
[Qdrant](https://qdrant.tech/). Every turn of the conversation is embedded and
stored as a vector; on each new message the most semantically similar past turns
are retrieved and fed back to the model as context. Memory therefore survives
process restarts.

## Stack

| Piece | Choice |
| --- | --- |
| API | FastAPI + Uvicorn |
| LLM | Claude Sonnet 5 via `langchain-anthropic` |
| Vector DB | Qdrant (Docker) |
| Embeddings | FastEmbed, `BAAI/bge-small-en-v1.5` (384-dim, local ONNX) |

Embeddings run locally through `qdrant-client`, so no second API key and no
Torch install. The ~130 MB model downloads on first use and is cached.

## Layout

```
app/
├── main.py              FastAPI app, mounts the router
├── api/routes.py        POST /chat
├── agents/chatbot.py    Chatbot: recall → store → invoke → store
├── llm/
│   ├── anthropic.py     ChatAnthropic singleton
│   └── prompts.py       SYSTEM_PROMPT, RECALL_PROMPT
├── vectorstore/
│   └── qdrant.py        Client, embedder, collection bootstrap, store/search
├── core/
│   ├── config.py        load_dotenv()
│   └── settings.py      All tunables, read from the environment
└── schemas/             ChatRequest, ChatResponse
```

## Setup

Requires Docker and Python 3.10+ (developed on 3.13).

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cp .env.example .env      # then set ANTHROPIC_API_KEY
```

Start Qdrant:

```bash
docker compose up -d
```

This brings up `qdrant/qdrant:v1.19.0` on ports 6333 (HTTP) and 6334 (gRPC),
with storage on a named volume so data outlives the container. Check it:

```bash
curl http://localhost:6333/healthz
```

The dashboard is at http://localhost:6333/dashboard.

Run the API:

```bash
.venv/bin/python -m uvicorn app.main:app --reload
```

Interactive docs at http://localhost:8000/docs.

## Usage

```bash
curl -X POST http://localhost:8000/chat \
  -H 'content-type: application/json' \
  -d '{"message": "My cat is named Biryani and she is a tabby."}'
```

```json
{ "response": "Biryani is a great name for a cat! ..." }
```

Restart the server and ask again — the answer comes from Qdrant, not from
in-process state:

```bash
curl -X POST http://localhost:8000/chat \
  -H 'content-type: application/json' \
  -d '{"message": "What is my cat called?"}'
```

```json
{ "response": "Your cat is named **Biryani**." }
```

## How memory works

Per call, `Chatbot.chat` does the following:

1. **Search** Qdrant for turns similar to the incoming message. This happens
   *before* the message is stored — otherwise the top hit would always be the
   message itself.
2. **Store** the user message as a point: the embedding plus a payload of
   `{role, text, session_id, created_at}`.
3. **Invoke** Claude with a system prompt that has the recalled excerpts
   appended, followed by this process's in-memory turns. Recall is folded into
   the single system prompt rather than sent as a second `SystemMessage`,
   because the Anthropic API takes `system` as one top-level field.
4. **Store** the reply the same way.

The collection (`chatbot` by default, 384-dim, cosine) is created on first use
by `ensure_collection()`.

Two message lists coexist: `self.messages` is the verbatim transcript for the
current process, giving exact short-term recall, while Qdrant holds every turn
ever seen and contributes fuzzy long-term recall. Restarting drops the former
and keeps the latter.

## Configuration

All settings live in `app/core/settings.py` and read from `.env`.

| Variable | Default | Meaning |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | — | Required. |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant endpoint. |
| `QDRANT_API_KEY` | unset | Only if you enable auth in `docker-compose.yml`. |
| `QDRANT_COLLECTION` | `chatbot` | Collection name. |
| `QDRANT_HTTP_PORT` | `6333` | Host port mapping (compose only). |
| `QDRANT_GRPC_PORT` | `6334` | Host port mapping (compose only). |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | Any FastEmbed model. Changing it changes the vector size, so drop the collection first. |
| `SEARCH_LIMIT` | `4` | Past turns retrieved per message. |

`MODEL_NAME` and `MAX_TOKENS` are set in `settings.py` directly rather than
through the environment.

## Inspecting the data

```bash
# collection stats
curl http://localhost:6333/collections/chatbot

# dump stored turns
curl -X POST http://localhost:6333/collections/chatbot/points/scroll \
  -H 'content-type: application/json' \
  -d '{"limit": 20, "with_payload": true, "with_vector": false}'

# wipe memory
curl -X DELETE http://localhost:6333/collections/chatbot
```

## Known limitations

- **Sessions are not isolated.** `session_id` is written to each payload but
  never filtered on at search time, so any conversation can recall any other.
  `routes.py` also holds a single module-level `Chatbot`, meaning all callers
  share one in-memory transcript. Both need fixing before multi-user use: add a
  session ID to `ChatRequest` and a Qdrant `Filter` on it.
- **In-memory history grows unbounded.** A long-lived process sends the entire
  transcript on every call, so token cost climbs. Needs a sliding window.
- **Qdrant auth is off by default.** Fine for local work; uncomment
  `QDRANT__SERVICE__API_KEY` in `docker-compose.yml` and set `QDRANT_API_KEY`
  before exposing it anywhere.
- **No tests.**
