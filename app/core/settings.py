import os

from app.core import config  # noqa: F401 - loads .env before os.getenv below

MODEL_NAME = "claude-sonnet-5"
MAX_TOKENS = 1024

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "chatbot")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
SEARCH_LIMIT = int(os.getenv("SEARCH_LIMIT", "4"))
