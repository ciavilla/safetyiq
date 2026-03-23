"""
claude_client.py
Handles all communication with the Claude API.

This is the core of SafetyIQ — we send Claude the user's question
plus the relevant chunks we retrieved from the database, and Claude
generates an accurate, cited answer.

KEY DESIGN DECISION — Why we constrain Claude to only use provided context:
Safety regulations are a domain where hallucination is unacceptable.
If Claude invents a regulation that doesn't exist, someone could get hurt.
By telling Claude to ONLY use the provided context and to always cite sources,
we ensure every answer is grounded in real OSHA documentation.
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# Initialize the Anthropic client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

if not os.getenv("ANTHROPIC_API_KEY"):
    raise ValueError("ANTHROPIC_API_KEY is not set in your .env file")

# The model to use — claude-sonnet is the best balance of quality and cost
MODEL = "claude-sonnet-4-20250514"

# ─────────────────────────────────────────────────────────
# SYSTEM PROMPT — This is the heart of the prompt engineering
#
# Notice:
# 1. We tell Claude exactly what role it plays
# 2. We explicitly forbid using knowledge outside the provided context
# 3. We require citations in a specific format
# 4. We tell Claude what to do when it doesn't know the answer
# 5. We include a safety disclaimer for emergencies
#
# These constraints are intentional design decisions, not limitations.
# ─────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are SafetyIQ, an AI assistant that answers workplace safety and OSHA compliance questions.

RULES:

1. Use the provided source documents as your primary source of information.
   Always prefer information from the provided context over general knowledge.

2. If the context contains PARTIAL information, use what you have and clearly
   note what additional standards the user should reference for a complete answer.

3. ALWAYS cite your sources using this exact format:
   [Source: Document Title, Page X]

4. Only say you don't have information if the context contains NOTHING relevant
   to the question. If there is any relevant information, use it and build on it.

5. Be practical and specific. Workers need actionable answers.

6. If the question describes an immediate safety emergency, begin with:
   "⚠️ If this is an immediate emergency, call 911 first."

7. Never invent specific regulation numbers or requirements not found in the context.
   But you MAY use general safety knowledge to supplement and frame the context."""


def ask_claude(question: str, context: str) -> str:
    """
    Sends a question + retrieved context to Claude and returns the answer.

    Args:
        question: The user's plain-English question
        context:  The formatted context string from retriever.format_context_for_prompt()

    Returns:
        Claude's answer as a string, with citations
    """

    # Build the user message — we include both the context and the question
    # The context goes first so Claude reads it before seeing the question
    user_message = f"""Here are the relevant sections from OSHA safety documents:

{context}

---

Based only on the documents above, please answer this question:
{question}"""

    # Send to Claude
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )

    # Extract the text from the response
    return response.content[0].text


def ask_claude_with_history(question: str, context: str, history: list[dict]) -> str:
    """
    Same as ask_claude but supports multi-turn conversation history.
    This lets users ask follow-up questions in the chat UI.

    Args:
        question: The user's current question
        context:  Retrieved context for this question
        history:  List of previous messages in format:
                  [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

    Returns:
        Claude's answer as a string
    """

    # Build the current user message with context
    current_message = f"""Here are the relevant sections from OSHA safety documents for this question:

{context}

---

Based only on the documents above, please answer this question:
{question}"""

    # Combine history with the current message
    messages = history + [{"role": "user", "content": current_message}]

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages
    )

    return response.content[0].text
