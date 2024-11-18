"""
Vector-based memory store implementation using scikit-learn for similarity search.
"""

from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from sklearn.neighbors import NearestNeighbors
import asyncio
from datetime import datetime
import json
from copy import deepcopy
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from ..base import BaseMemoryStore, MemoryEntry

class VectorStore(BaseMemoryStore):
    """Memory store implementation using vector embeddings and scikit-learn for semantic search."""

    def __init__(
        self,
        embedding_model: str = "text-embedding-ada-002",
        metric: str = "l2",
        dimension: int = 1536,  # Ada-002 embedding dimension
        n_neighbors: int = 10,  # Default number of neighbors to consider
        algorithm: str = "auto",  # Algorithm for nearest neighbors search
    ):
        """Initialize vector store.
        
        Args:
            embedding_model: OpenAI embedding model to use
            metric: Distance metric ('l2' or 'cosine')
            dimension: Embedding dimension
            n_neighbors: Number of neighbors to consider in search
            algorithm: Algorithm for nearest neighbors ('auto', 'ball_tree', 'kd_tree', or 'brute')
        """
        self._store: Dict[str, MemoryEntry] = {}
        self._lock = asyncio.Lock()
        self._embedding_model = embedding_model
        self._dimension = dimension
        self._n_neighbors = n_neighbors
        
        # Initialize nearest neighbors model
        self._nn = NearestNeighbors(
            n_neighbors=n_neighbors,
            metric="euclidean" if metric == "l2" else metric,
            algorithm=algorithm
        )
        
        # Initialize empty embeddings array
        self._embeddings = np.zeros((0, dimension), dtype=np.float32)
        self._id_to_index: Dict[str, int] = {}
        self._needs_fit = True

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding vector for text using OpenAI API."""
        response = await openai.Embedding.acreate(
            input=text,
            model=self._embedding_model
        )
        return np.array(response.data[0].embedding, dtype=np.float32)

    async def _ensure_model_fit(self):
        """Ensure nearest neighbors model is fit with current data."""
        if not self._needs_fit or len(self._store) == 0:
            return
            
        async with self._lock:
            if len(self._embeddings) > 0:
                self._nn.fit(self._embeddings)
                self._needs_fit = False

    async def add(self, entry: MemoryEntry) -> str:
        """Add a memory entry to the store."""
        async with self._lock:
            # Get embedding for entry content
            embedding = await self._get_embedding(str(entry.content))
            
            # Add to store
            self._store[entry.id] = entry
            
            # Add to embeddings array
            index = len(self._embeddings)
            self._id_to_index[entry.id] = index
            self._embeddings = np.vstack([self._embeddings, embedding])
            
            # Mark model for refitting
            self._needs_fit = True
            
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
        min_similarity: float = 0.7,
        **kwargs
    ) -> List[MemoryEntry]:
        """Search for memory entries using semantic similarity.
        
        Args:
            query: Search query string
            memory_type: Optional filter by memory type
            agent_id: Optional filter by agent ID
            limit: Maximum number of results to return
            min_similarity: Minimum cosine similarity threshold
            **kwargs: Additional search parameters
            
        Returns:
            List[MemoryEntry]: List of matching memory entries
        """
        await self._ensure_model_fit()
        
        async with self._lock:
            if len(self._store) == 0:
                return []
                
            # Get query embedding
            query_embedding = await self._get_embedding(query)
            
            # Perform similarity search
            if len(self._embeddings) > 0:
                distances, indices = self._nn.kneighbors(
                    query_embedding.reshape(1, -1),
                    n_neighbors=min(limit * 2, len(self._store))  # Get extra results for filtering
                )
                distances = distances[0]
                indices = indices[0]
            else:
                return []
            
            # Convert L2 distances to cosine similarities
            if self._nn.metric == "euclidean":
                # Convert L2 distance to cosine similarity
                similarities = 1 - (distances ** 2) / 2
            else:
                # Already cosine distances
                similarities = 1 - distances
            
            # Get entries and filter
            results = []
            for idx, sim in zip(indices, similarities):
                if sim < min_similarity:
                    continue
                    
                # Get entry ID from index
                entry_id = None
                for eid, eidx in self._id_to_index.items():
                    if eidx == idx:
                        entry_id = eid
                        break
                        
                if not entry_id:
                    continue
                    
                entry = self._store[entry_id]
                
                # Apply filters
                if memory_type and entry.memory_type != memory_type:
                    continue
                if agent_id and entry.agent_id != agent_id:
                    continue
                    
                # Add similarity score to metadata
                entry_copy = deepcopy(entry)
                entry_copy.metadata["similarity_score"] = float(sim)
                results.append(entry_copy)
                
                if len(results) >= limit:
                    break
                    
            return results

    async def update(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """Update a memory entry."""
        async with self._lock:
            if entry_id not in self._store:
                return False
                
            entry = self._store[entry_id]
            old_content = str(entry.content)
            
            # Update fields
            for key, value in updates.items():
                if hasattr(entry, key):
                    setattr(entry, key, value)
                    
            # Update embedding if content changed
            new_content = str(entry.content)
            if new_content != old_content:
                embedding = await self._get_embedding(new_content)
                idx = self._id_to_index[entry_id]
                self._embeddings[idx] = embedding
                self._needs_fit = True
                    
            # Update timestamp
            entry.timestamp = datetime.utcnow()
            return True

    async def delete(self, entry_id: str) -> bool:
        """Delete a memory entry."""
        async with self._lock:
            if entry_id not in self._store:
                return False
                
            # Remove from store
            del self._store[entry_id]
            
            # Remove from embeddings array
            idx = self._id_to_index[entry_id]
            mask = np.ones(len(self._embeddings), dtype=bool)
            mask[idx] = False
            self._embeddings = self._embeddings[mask]
            
            # Update index mapping
            del self._id_to_index[entry_id]
            for eid, eidx in self._id_to_index.items():
                if eidx > idx:
                    self._id_to_index[eid] = eidx - 1
                    
            # Mark model for refitting
            self._needs_fit = True
            
            return True

    async def clear(self) -> None:
        """Clear all entries from the store."""
        async with self._lock:
            self._store.clear()
            self._id_to_index.clear()
            self._embeddings = np.zeros((0, self._dimension), dtype=np.float32)
            self._needs_fit = True
