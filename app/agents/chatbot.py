import logging

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)


from app.llm.anthropic import llm
from app.llm.prompts import SYSTEM_PROMPT


class Chatbot:

    def __init__(self):

        self.messages = [
            SystemMessage(content=SYSTEM_PROMPT)
        ]

    def chat(self, text: str):

        try:

            self.messages.append(
                HumanMessage(content=text)
            )

            response = llm.invoke(self.messages)

            self.messages.append(response)

            return response.content

        except:
            logger.exception("Failed to generate chatbot response")

            return (
                "Sorry, I'm unable to process your request right now. "
                "Please try again later."
            )
