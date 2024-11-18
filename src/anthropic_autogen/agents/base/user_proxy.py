"""
User proxy agent implementations.
"""

from typing import Any, Dict, List, Optional, Union
from abc import abstractmethod

from autogen_core.base import AgentId, MessageContext
from autogen_core.components import message_handler

from ...core.agents.base import BaseAgent
from ...core.messaging import (
    ChatMessage,
    TaskMessage,
    SystemMessage,
    UserMessage,
    AssistantMessage
)


class BaseUserProxyAgent(BaseAgent):
    """Base class for user proxy agents."""

    def __init__(
        self,
        agent_id: AgentId,
        name: str = "User",
        description: str = "User proxy agent",
        **kwargs
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            **kwargs
        )

    @message_handler
    async def handle_chat(
        self,
        message: ChatMessage,
        context: MessageContext
    ) -> Optional[ChatMessage]:
        """Handle chat messages."""
        return await self.get_human_response(message)

    @message_handler
    async def handle_task(
        self,
        message: TaskMessage,
        context: MessageContext
    ) -> Optional[TaskMessage]:
        """Handle task messages."""
        return await self.get_human_response(message)

    @abstractmethod
    async def get_human_response(
        self,
        message: Union[ChatMessage, TaskMessage]
    ) -> Optional[Union[ChatMessage, TaskMessage]]:
        """Get response from human user.
        
        Args:
            message: Message to respond to
            
        Returns:
            Optional response message
        """
        pass


class InteractiveUserProxyAgent(BaseUserProxyAgent):
    """Interactive user proxy that prompts for input."""

    async def get_human_response(
        self,
        message: Union[ChatMessage, TaskMessage]
    ) -> Optional[Union[ChatMessage, TaskMessage]]:
        """Get response by prompting for input.
        
        Args:
            message: Message to respond to
            
        Returns:
            Response message
        """
        # Print received message
        print(f"\nReceived message from {message.sender}:")
        if isinstance(message, ChatMessage):
            print(message.content)
        elif isinstance(message, TaskMessage):
            print(f"Task: {message.task}")
            if message.parameters:
                print(f"Parameters: {message.parameters}")

        # Get input
        response = input("\nYour response: ")
        if not response:
            return None

        # Create response message
        if isinstance(message, ChatMessage):
            return ChatMessage(
                sender=self.id,
                recipient=message.sender,
                content=response,
                reply_to=message.id
            )
        else:
            response_msg = message.model_copy()
            response_msg.result = response
            return response_msg