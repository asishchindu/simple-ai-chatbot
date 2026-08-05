from fastapi import APIRouter

from app.agents.chatbot import Chatbot
from app.schemas.request import ChatRequest
from app.schemas.response import ChatResponse

router = APIRouter()

bot = Chatbot()


@router.post(
    "/chat",
    response_model=ChatResponse,
)
def chat(request: ChatRequest):

    answer = bot.chat(request.message)

    return ChatResponse(
        response=answer
    )