"""Tests for the enhanced runtime system."""

import pytest
from typing import List, Optional
import asyncio

from autogen_core.base import (
    Agent,
    AgentId,
    MessageContext,
    TopicId,
    CancellationToken,
    Subscription,
)

from anthropic_autogen.core.runtime_v2 import Runtime
from anthropic_autogen.memory.stores.in_memory import InMemoryStore


class TestAgent(Agent):
    """Simple test agent implementation."""
    
    def __init__(self, agent_id: str):
        self._id = AgentId(key=agent_id, type="test")
        self.received_messages = []
        
    @property
    def id(self) -> AgentId:
        """Get agent ID."""
        return self._id
        
    async def handle_message(self, message: str, context: MessageContext) -> None:
        """Handle received message."""
        self.received_messages.append(message)


@pytest.fixture
async def runtime():
    """Create runtime instance for testing."""
    return Runtime(memory_store=InMemoryStore())


@pytest.mark.asyncio
async def test_send_message(runtime: Runtime):
    """Test sending message between agents."""
    # Create test agents
    agent1 = TestAgent("agent1")
    agent2 = TestAgent("agent2")
    
    # Register agents
    await runtime.register(
        type="test_agent1",
        agent_factory=lambda: agent1
    )
    await runtime.register(
        type="test_agent2", 
        agent_factory=lambda: agent2
    )
    
    # Send message
    message = "Hello!"
    await runtime.send_message(
        message=message,
        sender=agent1.id,
        recipient=agent2.id
    )
    
    # Check message was received
    assert agent2.received_messages == [message]


@pytest.mark.asyncio
async def test_publish_message(runtime: Runtime):
    """Test publishing message to topic."""
    # Create test agents
    agent1 = TestAgent("agent1")
    agent2 = TestAgent("agent2")
    agent3 = TestAgent("agent3")
    
    # Create test topic
    topic = TopicId("test_topic", "test_source")
    
    # Register agents
    await runtime.register(
        type="test_agent1",
        agent_factory=lambda: agent1
    )
    await runtime.register(
        type="test_agent2",
        agent_factory=lambda: agent2
    )
    await runtime.register(
        type="test_agent3",
        agent_factory=lambda: agent3
    )
    
    # Subscribe agents to topic
    await runtime.subscribe(agent2.id, topic)
    await runtime.subscribe(agent3.id, topic)
    
    # Publish message
    message = "Hello subscribers!"
    await runtime.publish(
        message=message,
        topic=topic,
        publisher=agent1.id
    )
    
    # Verify message received by subscribers
    assert message in agent2.received_messages
    assert message in agent3.received_messages
    assert not agent1.received_messages  # Publisher doesn't receive message


@pytest.mark.asyncio
async def test_state_management(runtime: Runtime):
    """Test runtime state management."""
    # Add test metadata
    runtime._metadata["test"] = "value"
    
    # Save state
    state = await runtime.save_state()
    
    # Create new runtime
    new_runtime = Runtime(memory_store=InMemoryStore())
    
    # Load state
    await new_runtime.load_state(state)
    
    # Verify state loaded correctly
    assert new_runtime._metadata == {"test": "value"}
