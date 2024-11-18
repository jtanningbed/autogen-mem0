"""
Base memory system interfaces and implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime
from pydantic import BaseModel, Field

T = TypeVar('T')

class MemoryEntry(BaseModel, Generic[T]):
    """Base class for memory entries."""
    id: str = Field(description="Unique identifier for the memory entry")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    content: T = Field(description="Content of the memory entry")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the memory entry"
    )
    agent_id: Optional[str] = Field(
        default=None,
        description="ID of the agent that created this memory"
    )
    memory_type: str = Field(
        description="Type of memory (e.g., conversation, task, knowledge)"
    )

class BaseMemoryStore(ABC):
    """Abstract base class for memory storage backends."""

    @abstractmethod
    async def add(self, entry: MemoryEntry) -> str:
        """Add a memory entry to the store.
        
        Args:
            entry: The memory entry to store
            
        Returns:
            str: The ID of the stored entry
        """
        pass

    @abstractmethod
    async def get(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by ID.
        
        Args:
            entry_id: The ID of the entry to retrieve
            
        Returns:
            Optional[MemoryEntry]: The memory entry if found, None otherwise
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        memory_type: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 10,
        **kwargs
    ) -> List[MemoryEntry]:
        """Search for memory entries.
        
        Args:
            query: Search query string
            memory_type: Optional filter by memory type
            agent_id: Optional filter by agent ID
            limit: Maximum number of results to return
            **kwargs: Additional search parameters
            
        Returns:
            List[MemoryEntry]: List of matching memory entries
        """
        pass

    @abstractmethod
    async def update(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """Update a memory entry.
        
        Args:
            entry_id: ID of the entry to update
            updates: Dictionary of fields to update
            
        Returns:
            bool: True if update successful, False otherwise
        """
        pass

    @abstractmethod
    async def delete(self, entry_id: str) -> bool:
        """Delete a memory entry.
        
        Args:
            entry_id: ID of the entry to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        pass

class MemoryManager:
    """Manages memory operations and interactions with storage backend."""

    def __init__(self, store: BaseMemoryStore):
        self.store = store

    async def add_memory(
        self,
        content: Any,
        memory_type: str,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a new memory entry.
        
        Args:
            content: The content to store
            memory_type: Type of memory
            agent_id: Optional ID of the agent creating the memory
            metadata: Optional additional metadata
            
        Returns:
            str: ID of the created memory entry
        """
        entry = MemoryEntry(
            id=f"mem_{datetime.utcnow().timestamp()}",
            content=content,
            memory_type=memory_type,
            agent_id=agent_id,
            metadata=metadata or {}
        )
        return await self.store.add(entry)

    async def get_memory(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by ID."""
        return await self.store.get(entry_id)

    async def search_memories(
        self,
        query: str,
        memory_type: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 10,
        **kwargs
    ) -> List[MemoryEntry]:
        """Search for memory entries."""
        return await self.store.search(
            query,
            memory_type=memory_type,
            agent_id=agent_id,
            limit=limit,
            **kwargs
        )

    async def update_memory(
        self,
        entry_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update a memory entry."""
        return await self.store.update(entry_id, updates)

    async def delete_memory(self, entry_id: str) -> bool:
        """Delete a memory entry."""
        return await self.store.delete(entry_id)
