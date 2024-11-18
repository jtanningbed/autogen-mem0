"""
Base agent implementations for autogen-core integration.

This module provides base agent implementations that extend RoutedAgent with tool management
and message handling capabilities. The message handling pattern follows these principles:

1. Each message type has its own dedicated handler
2. Message handlers are decorated with @message_handler for routing
3. Agents explicitly declare which message types they support
4. No runtime type checking needed - routing is handled by the framework
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type

from autogen_core.base import MessageContext
from autogen_core.components import RoutedAgent, event, rpc, message_handler
from autogen_core.components.tools import Tool, ToolSchema

from ..messaging import ChatMessage, ToolMessage, SystemMessage, TaskMessage, UserMessage, AssistantMessage
from ..tools import BaseTool
from ..mixins import MemoryMixin, ConversationMixin

class BaseAgent(RoutedAgent, ABC):
    """Base agent implementation that extends RoutedAgent with tool management and message handling.
    
    This provides a foundation for building agents that can:
    1. Handle different types of messages through RoutedAgent's routing system
    2. Manage and execute tools
    3. Clean up resources properly
    """
    
    def __init__(
        self,
        description: str,
        tools: Optional[List[BaseTool]] = None,
        **kwargs
    ):
        """Initialize base agent.
        
        Args:
            description: Agent description and capabilities
            tools: Optional list of tools available to agent
            **kwargs: Additional agent configuration
        """
        super().__init__(description=description)
        
        # Initialize tools
        self._tools = {tool.name: tool for tool in tools} if tools else {}
                
    @property
    def tools(self) -> Dict[str, BaseTool]:
        """Get agent tools."""
        return self._tools

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool with the agent.
        
        Args:
            tool: Tool to register
        """
        self._tools[tool.name] = tool

    @classmethod
    def _handles_types(cls) -> List[Type[Any]]:
        """Get message types this agent handles.
        
        Returns:
            List of message types that this agent can handle
        """
        return [ChatMessage, ToolMessage, SystemMessage, TaskMessage, UserMessage, AssistantMessage]

    @message_handler
    async def handle_chat(self, message: ChatMessage, ctx: MessageContext) -> None:
        """Handle chat messages.
        
        Args:
            message: Chat message to handle
            ctx: Message context
        """
        pass

    @message_handler  
    async def handle_tool(self, message: ToolMessage, ctx: MessageContext) -> Any:
        """Handle tool messages.
        
        Args:
            message: Tool message to handle
            ctx: Message context
            
        Returns:
            Tool execution result
        """
        pass

    @message_handler
    async def handle_task(self, message: TaskMessage, ctx: MessageContext) -> None:
        """Handle task messages.
        
        Args:
            message: Task message to handle
            ctx: Message context
        """
        pass

    @message_handler
    async def handle_system(self, message: SystemMessage, ctx: MessageContext) -> None:
        """Handle system messages.
        
        Args:
            message: System message to handle
            ctx: Message context
        """
        pass

    @message_handler
    async def handle_user(self, message: UserMessage, ctx: MessageContext) -> None:
        """Handle user messages.
        
        Args:
            message: User message to handle
            ctx: Message context
        """
        pass

    @message_handler
    async def handle_assistant(self, message: AssistantMessage, ctx: MessageContext) -> None:
        """Handle assistant messages.
        
        Args:
            message: Assistant message to handle
            ctx: Message context
        """
        pass


class MemoryAgent(MemoryMixin, BaseAgent):
    """Agent with memory capabilities."""
    
    def __init__(
        self,
        description: str,
        tools: Optional[List[BaseTool]] = None,
        memory_store: Optional[Any] = None,
        **kwargs
    ):
        """Initialize memory agent.
        
        Args:
            description: Agent description and capabilities
            tools: Optional list of tools available to agent
            memory_store: Optional memory storage backend
            **kwargs: Additional agent configuration
        """
        super().__init__(description=description, tools=tools, **kwargs)
        self._memory_store = memory_store

    @event
    async def handle_chat(self, message: ChatMessage, ctx: MessageContext) -> None:
        """Handle chat messages with memory context.
        
        Args:
            message: Chat message to handle
            ctx: Message context
        """
        # Store message in memory
        await self.remember(message, context=ctx)


class ConversationalAgent(ConversationMixin, MemoryAgent):
    """Agent with conversation capabilities."""
    
    def __init__(
        self,
        description: str,
        tools: Optional[List[BaseTool]] = None,
        memory_store: Optional[Any] = None,
        **kwargs
    ):
        """Initialize conversational agent.
        
        Args:
            description: Agent description and capabilities
            tools: Optional list of tools available to agent
            memory_store: Optional memory storage backend
            **kwargs: Additional agent configuration
        """
        super().__init__(
            description=description,
            tools=tools,
            memory_store=memory_store,
            **kwargs
        )

    @event
    async def handle_chat(self, message: ChatMessage, ctx: MessageContext) -> None:
        """Handle chat messages with conversation capabilities.
        
        Args:
            message: Chat message to handle
            ctx: Message context
        """
        # Store in memory
        await super().handle_chat(message, ctx)
        
        # Generate response using conversation capabilities
        response = await self.generate_response(message, context=ctx)
        if response:
            self.publish_message(response, ctx.topic_id)
