import logging
import uuid
from datetime import datetime, timezone

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)

from app.core.settings import (
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    EMBEDDING_MODEL,
    SEARCH_LIMIT,
)

logger = logging.getLogger(__name__)

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)

embedder = TextEmbedding(model_name=EMBEDDING_MODEL)

VECTOR_SIZE = next(
    model["dim"]
    for model in TextEmbedding.list_supported_models()
    if model["model"] == EMBEDDING_MODEL
)


def ensure_collection():

    if client.collection_exists(QDRANT_COLLECTION):
        return

    client.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )

    logger.info("Created Qdrant collection %s", QDRANT_COLLECTION)


def embed(text: str):

    return next(iter(embedder.embed([text]))).tolist()


def store_message(role: str, text: str, session_id: str):

    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=embed(text),
        payload={
            "role": role,
            "text": text,
            "session_id": session_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    client.upsert(
        collection_name=QDRANT_COLLECTION,
        points=[point],
    )


def search_messages(text: str, limit: int = SEARCH_LIMIT):

    hits = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=embed(text),
        limit=limit,
        with_payload=True,
    ).points

    return [hit.payload for hit in hits]
