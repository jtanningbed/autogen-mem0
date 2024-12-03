"""Test memory-enabled Anthropic client with mem0 integration."""

import asyncio
from datetime import datetime
import logging
import pytest

from autogen_core.base import CancellationToken
from autogen_mem0.models import MemoryEnabledAnthropicClient
from autogen_mem0.core.messaging import (
    SystemMessage,
    UserMessage,
    AssistantMessage,
)

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TEST_USER_ID = "test_user_123"

@pytest.mark.asyncio
async def test_memory_enabled_client() -> None:
    """Test memory-enabled client with mem0."""
    logger.info("Starting test_memory_enabled_client")
    
    # Initialize client with in-memory vector store
    model = MemoryEnabledAnthropicClient(
        model="claude-3-opus-20240229",
        max_tokens=1024,
        vector_store_config={
            "provider": "memory",  # Use mem0's in-memory store
            "config": {}
        }
    )
    
    # Test sequence with memory context
    messages = [
        SystemMessage(
            content="This is a test conversation",
            metadata={"run_id": "test_run_1"}
        ),
        UserMessage(
            content="Remember that my favorite color is blue",
            metadata={"user_id": TEST_USER_ID}
        ),
        AssistantMessage(
            content="I'll remember that your favorite color is blue."
        ),
        UserMessage(
            content="What's my favorite color?",
            metadata={
                "user_id": TEST_USER_ID,
                "run_id": "test_run_1"
            }
        )
    ]
    
    # Process messages
    response = await model.create(messages, cancellation_token=CancellationToken())
    
    # Verify response
    assert response is not None
    assert isinstance(response, AssistantMessage)
    assert "blue" in response.content.lower()

if __name__ == "__main__":
    asyncio.run(test_memory_enabled_client())
