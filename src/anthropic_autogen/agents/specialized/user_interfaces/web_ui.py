"""
Web UI user proxy implementation.
"""

from typing import Optional, Union

from autogen_core.base import AgentId, MessageContext
from autogen_core.components import message_handler

from ...base import BaseUserProxyAgent
from ....core.messaging import ChatMessage, TaskMessage, UserMessage


class WebUIUserProxy(BaseUserProxyAgent):
    """Web UI user proxy that handles user interactions through a web interface."""

    def __init__(
        self,
        agent_id: AgentId,
        name: str = "Web UI",
        description: str = "Web UI user proxy agent",
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
        """Handle chat messages by simulating user interaction."""
        # For now, just echo back a simple response
        response = UserMessage(
            content="Acknowledged: " + message.content,
            metadata={"source": "web_ui"}
        )
        return response

    @message_handler
    async def handle_task(
        self,
        message: TaskMessage,
        context: MessageContext
    ) -> Optional[TaskMessage]:
        """Handle task messages by simulating user interaction."""
        # For now, just mark tasks as completed
        response = message.model_copy()
        response.result = "Task completed"
        return response
