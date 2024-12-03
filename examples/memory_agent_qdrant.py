"""Example demonstrating basic memory tool integration."""

import asyncio
from pathlib import Path
from dotenv import load_dotenv
import os

from autogen_core.base import CancellationToken
from autogen_agentchat.messages import TextMessage
from autogen_core.components.models import UserMessage
from autogen_mem0.core.config.manager import ConfigManager
from autogen_mem0.core.agents import AgentConfig, MemoryEnabledAssistant
from autogen_mem0.models import AnthropicChatCompletionClient
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

async def main():
    """Run memory agent example."""
    # Load environment variables
    load_dotenv()

    # Load configuration
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    config_manager = ConfigManager(config_path)

    # Get memory configuration
    memory_config = config_manager.get_memory_config()
    print(f"Memory config: {memory_config}")

    # Create Anthropic client with identity context
    client = AnthropicChatCompletionClient(
        model="claude-3-opus-20240229",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        config_manager=config_manager  # Pass config manager to client
    )

    # Create agent config with memory enabled
    agent_config = AgentConfig(
        name="memory_agent",
        description="An AI assistant with memory capabilities.",
        memory_config=memory_config,  # Pass memory config here
        context={
            "user_id": "test_user",
            "agent_id": "memory_agent",
            "session_id": "test_session"
        }
    )

    # Create memory-enabled agent
    agent = MemoryEnabledAssistant(
        config=agent_config,
        model_client=client
    )

    # Test basic memory storage and recall
    messages = [
        TextMessage(content="Hi! Let me tell you something important: The capital of France is Paris.", source="user"),
    ]
    
    response = await agent.on_messages(messages=messages, cancellation_token=CancellationToken())
    print(f"\nUser: {messages[0].content}")
    print(f"Assistant: {response.chat_message.content}")

    # Test memory recall
    recall_messages = [
        TextMessage(content="What did I tell you earlier about France?", source="user")
    ]
    
    response = await agent.on_messages(messages=recall_messages, cancellation_token=CancellationToken())
    print(f"\nUser: {recall_messages[0].content}")
    print(f"Assistant: {response.chat_message.content}")

    # Cleanup resources
    agent.close()

if __name__ == "__main__":
    asyncio.run(main())
