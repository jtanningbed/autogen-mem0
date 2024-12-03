"""Memory and conversation management for autogen-mem0."""

import logging
from typing import Dict, Optional, Any, List, Set
from datetime import datetime
from uuid import uuid4

from mem0 import Memory
from mem0.configs.base import MemoryConfig

from ..config import ConfigManager

logger = logging.getLogger(__name__)

class ConversationContext:
    """Tracks transient conversation state for active sessions.
    
    This class focuses on managing active conversation state that doesn't require persistence,
    such as current speaker and session metadata. Long-term relationship tracking is handled
    by the graph database.
    """
    
    def __init__(self, conversation_id: str):
        """Initialize conversation context.
        
        Args:
            conversation_id: Unique conversation identifier
        """
        self.id = conversation_id
        self.start_time = datetime.now()
        self.current_speaker: Optional[str] = None  # user/agent id
        self.active_participants: Set[str] = set()  # Currently active user/agent ids
        self.session_metadata: Dict[str, Any] = {
            "start_time": self.start_time,
            "last_activity": self.start_time,
            "message_count": 0,
            "turn_count": 0
        }
    
    def set_speaker(self, speaker_id: str) -> None:
        """Set the current speaker and update session state.
        
        Args:
            speaker_id: User or agent identifier
        """
        self.current_speaker = speaker_id
        self.active_participants.add(speaker_id)
        self.session_metadata["last_activity"] = datetime.now()
        self.session_metadata["turn_count"] += 1
    
    def add_message(self, message_type: str = "chat") -> None:
        """Track a new message in the conversation.
        
        Args:
            message_type: Type of message (e.g., "chat", "system", "function")
        """
        self.session_metadata["message_count"] += 1
        self.session_metadata["last_activity"] = datetime.now()
        
    def is_active(self, timeout_minutes: int = 30) -> bool:
        """Check if the conversation is still active based on last activity.
        
        Args:
            timeout_minutes: Minutes of inactivity before conversation is considered inactive
            
        Returns:
            True if conversation is active, False otherwise
        """
        if not self.session_metadata.get("last_activity"):
            return False
            
        elapsed = datetime.now() - self.session_metadata["last_activity"]
        return elapsed.total_seconds() < (timeout_minutes * 60)


class MemoryManager:
    """Manages memory instances and conversation context for agents."""

    def __init__(self, config: ConfigManager):
        """Initialize memory manager.
        
        Args:
            config: Configuration manager instance
        """
        self._config = config
        self._memory_instances: Dict[str, Memory] = {}
        self._conversations: Dict[str, ConversationContext] = {}
        self._closed = False

    def close(self):
        """Close all memory instances and cleanup resources."""
        if self._closed:
            return
            
        logger.debug("Cleaning up memory manager resources")
        for memory_id, memory in self._memory_instances.items():
            if hasattr(memory, 'graph'):
                memory.graph.close()
        self._memory_instances.clear()
        self._conversations.clear()
        self._closed = True

    def __del__(self):
        """Cleanup resources during garbage collection."""
        self.close()

    def start_conversation(
        self,
        initial_speaker: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> str:
        """Start a new conversation.
        
        Args:
            initial_speaker: Optional user/agent ID of initial speaker
            conversation_id: Optional conversation identifier
            
        Returns:
            Conversation ID
        """
        conv_id = conversation_id or str(uuid4())
        context = ConversationContext(conv_id)

        if initial_speaker:
            context.set_speaker(initial_speaker)

        self._conversations[conv_id] = context
        return conv_id

    def set_conversation_speaker(
        self,
        conversation_id: str,
        speaker_id: str
    ) -> None:
        """Set the current speaker for a conversation.
        
        Args:
            conversation_id: Conversation identifier
            speaker_id: User or agent ID of speaker
        """
        if conversation_id in self._conversations:
            self._conversations[conversation_id].set_speaker(speaker_id)

   
    def get_memory(
        self,
        user_id: str,
        env: Optional[str] = None,
        memory_config: Optional[MemoryConfig] = None,
        create_if_missing: bool = True
    ) -> Optional[Memory]:
        """Get or create a memory instance for a user.
        
        Args:
            user_id: Unique identifier for the user/agent
            env: Optional environment name
            memory_config: Optional explicit MemoryConfig. If not provided, will use config from ConfigManager
            create_if_missing: If True, create new instance when missing
            
        Returns:
            Memory instance if exists or created, None otherwise
        """
        cache_key = f"{env or self._config.config.default_environment}:{user_id}"

        if cache_key in self._memory_instances:
            return self._memory_instances[cache_key]

        if create_if_missing:
            # Use provided config or get from config manager
            config = memory_config or self._config.to_mem0_config(env)

            # Initialize memory instance
            memory = Memory(config=config)
            self._memory_instances[cache_key] = memory
            return memory

        return None

    def clear_memory(self, user_id: str, env: Optional[str] = None):
        """Clear memory for a specific user.
        
        Args:
            user_id: User ID to clear memory for
            env: Optional environment name
        """
        cache_key = f"{env or self._config._config.default_env}:{user_id}"

        if cache_key in self._memory_instances:
            memory = self._memory_instances[cache_key]
            memory.clear(filters={"user_id": user_id})
            del self._memory_instances[cache_key]

    def reset_memory_cache(self):
        """Reset the memory instance cache.
        
        Note: This does not delete persisted data, only clears runtime cache.
        """
        self._memory_instances.clear()

    def backup_memory(self, user_id: str, env: Optional[str] = None) -> str:
        """Create a backup of user's memory.
        
        Args:
            user_id: User ID to backup
            env: Optional environment name
            
        Returns:
            Path to backup file
        """
        memory = self.get_memory(user_id, env)
        if not memory:
            raise ValueError(f"No memory found for user {user_id}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"backups/{user_id}_{timestamp}.mem0"

        # TODO: Implement backup functionality
        # memory.export(backup_path)

        return backup_path

    def restore_memory(self, user_id: str, backup_path: str, env: Optional[str] = None):
        """Restore memory from backup.
        
        Args:
            user_id: User ID to restore to
            backup_path: Path to backup file
            env: Optional environment name
        """
        # Clear existing memory
        self.clear_memory(user_id, env)

        # Create new memory instance
        memory = self.get_memory(user_id, env)

        # TODO: Implement restore functionality
        # memory.import_from(backup_path)

    def get_memory_stats(self, user_id: str, env: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about user's memory.
        
        Args:
            user_id: User ID to get stats for
            env: Optional environment name
            
        Returns:
            Dictionary of memory statistics
        """
        memory = self.get_memory(user_id, env)
        if not memory:
            raise ValueError(f"No memory found for user {user_id}")

        # TODO: Implement memory statistics
        stats = {
            "total_entries": 0,  # memory.count()
            "last_updated": None,  # memory.last_updated
            "size_bytes": 0,  # memory.size
        }

        return stats

    def optimize_memory(self, user_id: str, env: Optional[str] = None):
        """Optimize memory storage and retrieval.
        
        Args:
            user_id: User ID to optimize for
            env: Optional environment name
        """
        memory = self.get_memory(user_id, env)
        if not memory:
            raise ValueError(f"No memory found for user {user_id}")

        # TODO: Implement memory optimization
        # - Compact vector store
        # - Remove duplicates
        # - Update indices
        # memory.optimize()

    def search_memory(
        self,
        user_id: str,
        query: str,
        env: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Advanced memory search with filters and options.
        
        Args:
            user_id: User ID to search in
            query: Search query
            env: Optional environment name
            **kwargs: Additional search parameters
            
        Returns:
            List of matching memory entries
        """
        memory = self.get_memory(user_id, env)
        if not memory:
            raise ValueError(f"No memory found for user {user_id}")

        # TODO: Implement advanced search
        # results = memory.search(
        #     query,
        #     filters=kwargs.get("filters"),
        #     limit=kwargs.get("limit", 10),
        #     threshold=kwargs.get("threshold", 0.7)
        # )

        return []  # results