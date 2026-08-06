import logging
import uuid

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)


from app.llm.anthropic import llm
from app.llm.prompts import SYSTEM_PROMPT, RECALL_PROMPT
from app.vectorstore.qdrant import (
    ensure_collection,
    search_messages,
    store_message,
)

logger = logging.getLogger(__name__)


class Chatbot:

    def __init__(self):

        self.session_id = str(uuid.uuid4())

        self.messages = []

        ensure_collection()

    def system_message(self, text: str):

        recalled = search_messages(text)

        if not recalled:
            return SystemMessage(content=SYSTEM_PROMPT)

        history = "\n".join(
            f"- {item['role']}: {item['text']}"
            for item in recalled
        )

        return SystemMessage(
            content=SYSTEM_PROMPT + RECALL_PROMPT.format(history=history)
        )

    def chat(self, text: str):

        try:

            # Search before storing, so the new message is not recalled as context.
            system = self.system_message(text)

            store_message("user", text, self.session_id)

            self.messages.append(
                HumanMessage(content=text)
            )

            response = llm.invoke([system] + self.messages)

            self.messages.append(response)

            # .content may be a list of content blocks; .text is always a string.
            answer = response.text

            store_message("assistant", answer, self.session_id)

            return answer

        except Exception:
            logger.exception("Failed to generate chatbot response")

            return (
                "Sorry, I'm unable to process your request right now. "
                "Please try again later."
            )
