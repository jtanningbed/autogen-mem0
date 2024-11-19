"""Test fixtures for agent tests."""

import pytest
from autogen_core.application import SingleThreadedAgentRuntime
from autogen_core.base import TopicId, AgentType

from .test_agents import TestAgent, ToolOnlyAgent, ChatOnlyAgent
from .test_models import TestTool


@pytest.fixture
def test_topic_type() -> str:
    """Get test topic type."""
    return "test_topic"


@pytest.fixture
def test_tool() -> TestTool:
    """Get test tool."""
    return TestTool()


@pytest.fixture
def runtime() -> SingleThreadedAgentRuntime:
    """Get agent runtime."""
    return SingleThreadedAgentRuntime()


@pytest.fixture
async def base_agent(runtime: SingleThreadedAgentRuntime, test_topic_type: str) -> AgentType:
    """Get base agent."""
    return await TestAgent.register(
        runtime,
        test_topic_type,
        lambda: TestAgent(type_name=test_topic_type)
    )


@pytest.fixture
async def tool_only_agent(runtime: SingleThreadedAgentRuntime) -> AgentType:
    """Get tool-only agent."""
    return await ToolOnlyAgent.register(
        runtime,
        "tool_agent",
        lambda: ToolOnlyAgent()
    )


@pytest.fixture
async def chat_only_agent(runtime: SingleThreadedAgentRuntime) -> AgentType:
    """Get chat-only agent."""
    return await ChatOnlyAgent.register(
        runtime,
        "chat_agent",
        lambda: ChatOnlyAgent()
    )
