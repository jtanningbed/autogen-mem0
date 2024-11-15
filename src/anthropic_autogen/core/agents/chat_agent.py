from typing import Set, Optional, List
from abc import abstractmethod
from autogen_core.base import CancellationToken

from .base import BaseAgent
from ..messaging import (
    Message, MessageCategory, ChatMessage
)

class ChatAgent(BaseAgent):
    """Agent for chat-based interactions"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._conversation_history: List[ChatMessage] = []

    def get_subscribed_categories(self) -> Set[MessageCategory]:
        return {MessageCategory.CHAT}

    async def handle_message(
        self,
        message: Message,
        cancellation_token: Optional[CancellationToken] = None
    ) -> None:
        if not isinstance(message, ChatMessage):
            return

        # Store message in conversation history
        self._conversation_history.append(message)

        # Handle message based on content
        response = await self._generate_response(message, cancellation_token)
        if response:
            await self.send_message(response, cancellation_token)

    @abstractmethod
    async def _generate_response(
        self,
        message: ChatMessage,
        cancellation_token: Optional[CancellationToken] = None
    ) -> Optional[ChatMessage]:
        """Generate response to chat message"""
        pass

    def get_conversation_history(self) -> List[ChatMessage]:
        """Get conversation history"""
        return self._conversation_history.copy()

    def clear_conversation_history(self) -> None:
        """Clear conversation history"""
        self._conversation_history.clear()
