"""
In-memory implementation of the memory storage backend.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from copy import deepcopy

from ..base import BaseMemoryStore, MemoryEntry

class InMemoryStore(BaseMemoryStore):
    """Simple in-memory implementation of memory storage."""

    def __init__(self):
        self._store: Dict[str, MemoryEntry] = {}
        self._lock = asyncio.Lock()

    async def add(self, entry: MemoryEntry) -> str:
        """Add a memory entry to the store."""
        async with self._lock:
            self._store[entry.id] = entry
            return entry.id

    async def get(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry by ID."""
        async with self._lock:
            entry = self._store.get(entry_id)
            if entry:
                return deepcopy(entry)
            return None

    async def search(
        self,
        query: str,
        memory_type: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 10,
        **kwargs
    ) -> List[MemoryEntry]:
        """Search for memory entries.
        
        This implementation does a simple substring search on the string
        representation of the content. More sophisticated implementations
        should use proper search indexing.
        """
        async with self._lock:
            results = []
            query = query.lower()
            
            for entry in self._store.values():
                # Apply filters
                if memory_type and entry.memory_type != memory_type:
                    continue
                if agent_id and entry.agent_id != agent_id:
                    continue
                    
                # Simple substring search
                if query in str(entry.content).lower():
                    results.append(deepcopy(entry))
                    
                if len(results) >= limit:
                    break
                    
            # Sort by timestamp descending
            results.sort(key=lambda x: x.timestamp, reverse=True)
            return results

    async def update(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """Update a memory entry."""
        async with self._lock:
            if entry_id not in self._store:
                return False
                
            entry = self._store[entry_id]
            
            # Update fields
            for key, value in updates.items():
                if hasattr(entry, key):
                    setattr(entry, key, value)
                    
            # Update timestamp
            entry.timestamp = datetime.utcnow()
            return True

    async def delete(self, entry_id: str) -> bool:
        """Delete a memory entry."""
        async with self._lock:
            if entry_id in self._store:
                del self._store[entry_id]
                return True
            return False

    async def clear(self) -> None:
        """Clear all entries from the store."""
        async with self._lock:
            self._store.clear()
