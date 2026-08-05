from langchain_anthropic import ChatAnthropic

from app.core.settings import (
    MODEL_NAME,
    MAX_TOKENS,
)

llm = ChatAnthropic(
    model=MODEL_NAME,
    max_tokens=MAX_TOKENS,
)
