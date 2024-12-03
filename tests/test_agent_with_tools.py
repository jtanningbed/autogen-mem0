"""Test agent with tool capabilities."""

import asyncio
from datetime import datetime
import logging
import pytest

from dotenv import load_dotenv
import os

from autogen_core.base import CancellationToken
from autogen_core.components.tools import FunctionTool
from autogen_mem0.models import AnthropicChatCompletionClient
from autogen_mem0.core.agents._base import AgentConfig, MemoryEnabledAssistant
from autogen_mem0.core.messaging import (
    SystemMessage,
    UserMessage,
    AssistantMessage
)

from autogen_agentchat.messages import TextMessage

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def get_current_time() -> str:
    """Get the current time."""
    current_time = datetime.now().strftime("%H:%M:%S")
    logger.info(f"[TOOL] get_current_time called, returning: {current_time}")
    return current_time

@pytest.mark.asyncio
async def test_agent_with_tools() -> None:
    """Test a MemoryEnabledAssistant using time tool."""
    load_dotenv()
    logger.info("Starting test_agent_with_tools")

    # Initialize model client
    model = AnthropicChatCompletionClient(
        model="claude-3-opus-20240229",
        max_tokens=1024, 
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    # Create agent with time tool
    agent = MemoryEnabledAssistant(
        config=AgentConfig(
            name="time_agent",
            description="A test agent with time capabilities"
        ),
        model_client=model,
        system_message="You are a helpful assistant that can tell the time.",
        tools=[
            FunctionTool(get_current_time, description="Get the current time")
        ]
    )

    # Test sequence
    messages = [
        SystemMessage(
            content="This is a test conversation"
        ),
        UserMessage(
            content="What time is it?"
        )
    ]

    # Process messages
    response = await agent.on_messages(messages, CancellationToken())

    # Verify response
    assert response is not None
    assert isinstance(response.chat_message, TextMessage)
    assert "time" in response.chat_message.content.lower()

if __name__ == "__main__":
    asyncio.run(test_agent_with_tools())
