"""Vector memory tools."""

from typing import Any, Dict, List, Optional
from autogen_core.components.tools._base import CancellationToken
from autogen_mem0.core.tools import BaseTool
from mem0 import Memory

from .models import SemanticSearchInput

class VectorSearchTool(BaseTool):
    """Tool for semantic search in vector memory."""

    def __init__(self, memory: Memory):
        if not memory.config.vector_store and not memory.config.vector_store.config:
            raise ValueError("Vector store is not enabled")
            
        super().__init__(
            args_type=SemanticSearchInput,
            return_type=List[Dict[str, Any]],
            name="vector_search",
            description="Perform semantic search in the vector store."
        )
        self.memory = memory

    async def run(self, args: SemanticSearchInput, cancellation_token: Optional[CancellationToken] = None) -> List[Dict[str, Any]]:
        """Search vector store."""
        filters = {}
        if args.user_id:
            filters["user_id"] = args.user_id
        if args.agent_id:
            filters["agent_id"] = args.agent_id
        if args.run_id:
            filters["run_id"] = args.run_id

        results = await self.memory.search(
            query=args.query,
            limit=args.limit,
            store_type="vector",
            **filters
        )
        return results.get("vector", [])