from fastapi import FastAPI

from app.core.config import *
from app.api.routes import router

app = FastAPI(
    title="LangChain Chatbot"
)

app.include_router(router)