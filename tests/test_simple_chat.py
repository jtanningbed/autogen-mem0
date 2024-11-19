import asyncio
import os
import logging
from typing import List

from autogen_core.components.models import LLMMessage, UserMessage, SystemMessage
from anthropic_autogen.models import AnthropicChatCompletionClient

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable debug logging for our module
logging.getLogger('anthropic_autogen').setLevel(logging.DEBUG)

async def test_simple_chat():
    logger = logging.getLogger(__name__)
    
    # Initialize the client
    client = AnthropicChatCompletionClient(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model="claude-3-opus-20240229",
        temperature=0.7,
        max_tokens=1024,
    )
    
    logger.debug("Client initialized")
    
    # Create a simple conversation
    messages: List[LLMMessage] = [
        SystemMessage(content="You are a helpful AI assistant."),
        UserMessage(content="What is the capital of France?", source="user")
    ]
    
    logger.debug("Messages created: %s", messages)
    
    # Get completion
    try:
        result = await client.create(messages)
        logger.debug("Got result: %s", result.content)
        print(f"Response: {result.content}")
    except Exception as e:
        logger.error("Error getting completion: %s", str(e), exc_info=True)
        raise
    
    # Test streaming
    print("\nStreaming response:")
    try:
        async for chunk in client.create_stream(messages):
            if isinstance(chunk, str):
                print(chunk, end="", flush=True)
    except Exception as e:
        logger.error("Error streaming completion: %s", str(e), exc_info=True)
        raise
    print("\n")

if __name__ == "__main__":
    asyncio.run(test_simple_chat())
