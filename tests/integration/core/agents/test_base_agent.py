"""Test base agent implementation."""

import pytest
from autogen_core.base import MessageContext, TopicId, AgentType, CancellationToken
from autogen_core.components import TypeSubscription
from autogen_core.application import SingleThreadedAgentRuntime

from anthropic_autogen.core.messaging import ChatMessage, ToolMessage

from .test_models import GroupChatMessage, TestTool
from .test_agents import TestAgent, ToolOnlyAgent, ChatOnlyAgent


class TestBaseAgentIntegration:
    """Test base agent integration."""

    def _create_message_context(self, topic_type: str, source: str = "test") -> MessageContext:
        """Create message context for testing."""
        return MessageContext(
            topic_id=TopicId(topic_type, source),
            sender=None,
            is_rpc=False,
            cancellation_token=CancellationToken()
        )

    async def test_agent_interface(
            self,
            runtime: SingleThreadedAgentRuntime,
            base_agent: AgentType,
            test_topic_type: str
        ):
        """Test agent interface."""
        agent = await runtime.try_get_underlying_agent_instance(base_agent, TestAgent)
        ctx = self._create_message_context(test_topic_type)

        # Test chat message handling
        chat_message = ChatMessage(content="test")
        await agent.handle_chat(chat_message, ctx)
        agent.handle_chat_mock.assert_called_once_with(chat_message)
        assert chat_message in agent.messages_received

        # Test tool message handling
        tool_message = ToolMessage(tool_name="test_tool", args={})
        result = await agent.handle_tool(tool_message, ctx)
        agent.handle_tool_mock.assert_called_once_with(tool_message)
        assert tool_message in agent.messages_received
        assert result == {"success": True}

        # Test group chat message handling
        group_message = GroupChatMessage(content="test", sender="test_sender")
        await agent.handle_group_message(group_message, ctx)
        agent.handle_group_mock.assert_called_once_with(group_message)
        assert group_message in agent.messages_received

    async def test_message_type_support(
            self,
            runtime: SingleThreadedAgentRuntime,
            base_agent: AgentType,
            tool_only_agent: AgentType,
            chat_only_agent: AgentType,
            test_topic_type: str
        ):
        """Test message type support detection."""
        agent = await runtime.try_get_underlying_agent_instance(base_agent, TestAgent)
        tool_agent = await runtime.try_get_underlying_agent_instance(tool_only_agent, ToolOnlyAgent)
        chat_agent = await runtime.try_get_underlying_agent_instance(chat_only_agent, ChatOnlyAgent)

        # Test base agent handles all types
        assert ChatMessage in [t[0] for t in agent._handles_types()]
        assert ToolMessage in [t[0] for t in agent._handles_types()]
        assert GroupChatMessage in [t[0] for t in agent._handles_types()]

        # Test specialized agents
        assert ToolMessage in [t[0] for t in tool_agent._handles_types()]
        assert ChatMessage not in [t[0] for t in tool_agent._handles_types()]

        assert ChatMessage in [t[0] for t in chat_agent._handles_types()]
        assert ToolMessage not in [t[0] for t in chat_agent._handles_types()]

    async def test_message_routing(
            self,
            runtime: SingleThreadedAgentRuntime,
            base_agent: AgentType,
            test_topic_type: str
        ):
        """Test message routing."""
        agent = await runtime.try_get_underlying_agent_instance(base_agent, TestAgent)
        ctx = self._create_message_context(test_topic_type)

        # Test chat message routing
        chat_message = ChatMessage(content="test")
        await agent.on_message(chat_message, ctx)
        agent.handle_chat_mock.assert_called_once_with(chat_message)
        assert chat_message in agent.messages_received

        # Test tool message routing
        tool_message = ToolMessage(tool_name="test_tool", args={})
        await agent.on_message(tool_message, ctx)
        agent.handle_tool_mock.assert_called_once_with(tool_message)
        assert tool_message in agent.messages_received

        # Test group chat message routing
        group_message = GroupChatMessage(content="test", sender="test_sender")
        await agent.on_message(group_message, ctx)
        agent.handle_group_mock.assert_called_once_with(group_message)
        assert group_message in agent.messages_received

    async def test_specialized_agents(
            self,
            runtime: SingleThreadedAgentRuntime,
            tool_only_agent: AgentType,
            chat_only_agent: AgentType,
            test_topic_type: str
        ):
        """Test specialized agents handle only their message types."""
        tool_agent = await runtime.try_get_underlying_agent_instance(tool_only_agent, ToolOnlyAgent)
        chat_agent = await runtime.try_get_underlying_agent_instance(chat_only_agent, ChatOnlyAgent)
        ctx = self._create_message_context(test_topic_type)

        # Test tool-only agent
        tool_message = ToolMessage(tool_name="test_tool", args={})
        await tool_agent.handle_tool(tool_message, ctx)
        tool_agent.handle_tool_mock.assert_called_once_with(tool_message)

        # Test chat-only agent
        chat_message = ChatMessage(content="test")
        await chat_agent.handle_chat(chat_message, ctx)
        chat_agent.handle_chat_mock.assert_called_once_with(chat_message)
