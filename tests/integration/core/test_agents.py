"""Test agent implementations."""

from typing import List, Type, Any, Tuple
from unittest.mock import AsyncMock

from autogen_core.base import MessageContext, MessageSerializer
from autogen_core.base._serialization import PydanticJsonMessageSerializer
from autogen_core.components import message_handler

from anthropic_autogen.core.messaging import ChatMessage, ToolMessage, MessageCommon
from anthropic_autogen.core.agents import BaseAgent

from .test_models import GroupChatMessage


class TestAgent(BaseAgent):
    """Test agent implementation that supports all message types."""
    
    def __init__(self, type_name: str = "test_agent"):
        """Initialize test agent."""
        super().__init__(description=type_name)
        self._handle_chat = AsyncMock()
        self._handle_tool = AsyncMock(return_value={"success": True})
        self._handle_group = AsyncMock()
        self.messages_received: List[MessageCommon] = []

    @property
    def handle_chat_mock(self):
        """Get handle_chat mock."""
        return self._handle_chat

    @property
    def handle_tool_mock(self):
        """Get handle_tool mock."""
        return self._handle_tool

    @property
    def handle_group_mock(self):
        """Get handle_group mock."""
        return self._handle_group

    @classmethod
    def _handles_types(cls) -> List[Tuple[Type[Any], MessageSerializer]]:
        """Get message types this agent handles."""
        return [(t, PydanticJsonMessageSerializer(t)) for t in [ChatMessage, ToolMessage, GroupChatMessage]]

    @message_handler
    async def handle_chat(self, message: ChatMessage, ctx: MessageContext) -> None:
        """Handle chat messages."""
        self.messages_received.append(message)
        await self._handle_chat(message)

    @message_handler
    async def handle_tool(self, message: ToolMessage, ctx: MessageContext) -> dict:
        """Handle tool messages."""
        self.messages_received.append(message)
        return await self._handle_tool(message)

    @message_handler
    async def handle_group_message(self, message: GroupChatMessage, ctx: MessageContext) -> None:
        """Handle group chat messages."""
        self.messages_received.append(message)
        await self._handle_group(message)


class ToolOnlyAgent(BaseAgent):
    """Test agent that only handles tool messages."""
    
    def __init__(self):
        """Initialize tool-only agent."""
        super().__init__(description="tool_only_agent")
        self._handle_tool = AsyncMock(return_value={"success": True})

    @property
    def handle_tool_mock(self):
        """Get handle_tool mock."""
        return self._handle_tool

    @classmethod
    def _handles_types(cls) -> List[Tuple[Type[Any], MessageSerializer]]:
        """Get message types this agent handles."""
        return [(ToolMessage, PydanticJsonMessageSerializer(ToolMessage))]

    @message_handler
    async def handle_tool(self, message: ToolMessage, ctx: MessageContext) -> dict:
        """Handle tool messages."""
        return await self._handle_tool(message)


class ChatOnlyAgent(BaseAgent):
    """Test agent that only handles chat messages."""
    
    def __init__(self):
        """Initialize chat-only agent."""
        super().__init__(description="chat_only_agent")
        self._handle_chat = AsyncMock()

    @property
    def handle_chat_mock(self):
        """Get handle_chat mock."""
        return self._handle_chat

    @classmethod
    def _handles_types(cls) -> List[Tuple[Type[Any], MessageSerializer]]:
        """Get message types this agent handles."""
        return [(ChatMessage, PydanticJsonMessageSerializer(ChatMessage))]

    @message_handler
    async def handle_chat(self, message: ChatMessage, ctx: MessageContext) -> None:
        """Handle chat messages."""
        await self._handle_chat(message)
