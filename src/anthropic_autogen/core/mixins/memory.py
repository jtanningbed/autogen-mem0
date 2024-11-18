"""
Mixin providing memory capabilities for agents.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from ...memory import BaseMemoryStore, MemoryEntry, InMemoryStore


class MemoryMixin:
    """Mixin providing memory capabilities."""
    
    def __init__(
        self,
        memory_store: Optional[BaseMemoryStore] = None,
        **kwargs
    ):
        """Initialize memory mixin.
        
        Args:
            memory_store: Memory storage backend
            **kwargs: Additional configuration
        """
        self.memory = memory_store or InMemoryStore()
        self.metadata: Dict[str, Any] = {}
        super().__init__(**kwargs)
        
    async def remember(
        self,
        content: Any,
        memory_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a memory entry.
        
        Args:
            content: Content to remember
            memory_type: Type of memory
            metadata: Optional metadata
            
        Returns:
            ID of stored memory
        """
        entry = MemoryEntry(
            id=f"mem_{datetime.now().isoformat()}",
            content=content,
            memory_type=memory_type,
            metadata=metadata or {},
            agent_id=getattr(self, 'agent_id', None)
        )
        return await self.memory.add(entry)
        
    async def recall(
        self,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
        **kwargs
    ) -> List[MemoryEntry]:
        """Search memory entries.
        
        Args:
            query: Search query
            memory_type: Optional memory type filter
            limit: Maximum results
            **kwargs: Additional search parameters
            
        Returns:
            List of matching memory entries
        """
        return await self.memory.search(
            query=query,
            memory_type=memory_type,
            agent_id=getattr(self, 'agent_id', None),
            limit=limit,
            **kwargs
        )
        
    async def cleanup(self) -> None:
        """Clean up memory resources."""
        await super().cleanup()
