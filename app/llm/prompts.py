SYSTEM_PROMPT = """
You are a helpful AI assistant.

Rules:

- Answer clearly.
- Keep responses concise.
- If you don't know something, say so.
"""

RECALL_PROMPT = """
Relevant excerpts from earlier conversations, retrieved by similarity to the
current message. They may be unrelated - use them only if they help.

{history}
"""
