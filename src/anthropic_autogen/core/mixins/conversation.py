"""
Mixin providing conversation capabilities with memory integration.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from .memory import MemoryMixin
from ..messaging import MessageCommon


class ConversationMixin(MemoryMixin):
    """Mixin providing conversation capabilities with memory integration."""

    def __init__(
        self,
        memory_store: Optional[Any] = None,
        **kwargs
    ):
        """Initialize conversation mixin.
        
        Args:
            memory_store: Memory storage backend
            **kwargs: Additional configuration
        """
        super().__init__(memory_store=memory_store, **kwargs)
        self.active_conversations: Dict[str, List[MessageCommon]] = {}

    async def start_conversation(
        self,
        initiator: str,
        participants: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start a new conversation between agents.
        
        Args:
            initiator: ID of agent starting conversation
            participants: List of participating agent IDs
            metadata: Optional conversation metadata
            
        Returns:
            Conversation ID
        """
        conv_id = f"conv_{len(self.active_conversations)}_{datetime.now().isoformat()}"
        self.active_conversations[conv_id] = []

        if metadata:
            self.metadata[conv_id] = metadata

        return conv_id

    async def send_message(self, message: MessageCommon, conversation_id: str) -> None:
        """Send a message in a conversation.
        
        Args:
            message: Message to send
            conversation_id: ID of conversation
        """
        if conversation_id not in self.active_conversations:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Store in conversation history
        self.active_conversations[conversation_id].append(message)

        # Store in memory
        await self.remember(
            content=message,
            memory_type="conversation",
            metadata={
                "conversation_id": conversation_id,
                "timestamp": message.timestamp
            }
        )

        # Let parent class handle message routing
        await super().send_message(message)

    async def get_conversation_history(
        self,
        conversation_id: str,
        include_memory: bool = False
    ) -> List[MessageCommon]:
        """Get history of messages in a conversation.
        
        Args:
            conversation_id: ID of conversation
            include_memory: Whether to include messages from memory
            
        Returns:
            List of messages in conversation
        """
        if conversation_id not in self.active_conversations:
            raise ValueError(f"Conversation {conversation_id} not found")

        history = self.active_conversations[conversation_id]

        if include_memory:
            memory_messages = await self.recall(
                query="",
                memory_type="conversation",
                metadata={"conversation_id": conversation_id}
            )

            for entry in memory_messages:
                if entry.content not in history:
                    history.append(entry.content)

            history.sort(key=lambda x: x.timestamp)

        return history

    async def end_conversation(self, conversation_id: str) -> None:
        """End a conversation.
        
        Args:
            conversation_id: ID of conversation to end
        """
        if conversation_id not in self.active_conversations:
            raise ValueError(f"Conversation {conversation_id} not found")

        del self.active_conversations[conversation_id]
        if conversation_id in self.metadata:
            del self.metadata[conversation_id]

    async def cleanup(self) -> None:
        """Clean up conversation resources."""
        # End all conversations
        for conv_id in list(self.active_conversations.keys()):
            await self.end_conversation(conv_id)

        await super().cleanup()
