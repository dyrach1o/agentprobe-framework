"""Conversation testing example: Multi-turn ConversationRunner.

This example demonstrates how to:
1. Set up a multi-turn conversation test
2. Use ConversationRunner with a mock adapter
3. Validate conversation flow

Usage:
    python examples/conversation_testing.py
"""

from __future__ import annotations

import asyncio
from typing import Any

from agentprobe.core.conversation import ConversationRunner
from agentprobe.core.models import Trace


# ── Multi-turn adapter ──
class ChatbotAdapter:
    """A demo chatbot that tracks conversation state."""

    def __init__(self) -> None:
        self._history: list[str] = []

    @property
    def name(self) -> str:
        return "chatbot-demo"

    async def invoke(self, input_text: str, **kwargs: Any) -> Trace:
        self._history.append(input_text)
        turn_count = len(self._history)

        if turn_count == 1:
            response = "Hello! How can I help you today?"
        elif "order" in input_text.lower():
            response = "I can help with your order. What's your order number?"
        elif any(c.isdigit() for c in input_text):
            response = f"Found order details for: {input_text}. Status: shipped."
        else:
            response = f"You said: {input_text}. How can I help further?"

        return Trace(
            agent_name=self.name,
            input_text=input_text,
            output_text=response,
        )


async def main() -> None:
    """Run the conversation testing example."""
    adapter = ChatbotAdapter()
    runner = ConversationRunner(adapter=adapter)

    # Define a multi-turn conversation
    turns = [
        "Hello",
        "I need help with my order",
        "Order #12345",
    ]

    print("Conversation Test")
    print("=" * 50)

    traces: list[Trace] = []
    for user_msg in turns:
        print(f"\n  User:  {user_msg}")
        trace = await runner.send(user_msg)
        traces.append(trace)
        print(f"  Agent: {trace.output_text}")

    print(f"\n{'=' * 50}")
    print(f"Total turns: {len(traces)}")
    print("All turns completed successfully.")

    # Verify conversation flow
    assert "help" in traces[0].output_text.lower()
    assert "order" in traces[1].output_text.lower()
    assert "shipped" in traces[2].output_text.lower()
    print("Assertions passed: conversation flow is correct.")


if __name__ == "__main__":
    asyncio.run(main())
