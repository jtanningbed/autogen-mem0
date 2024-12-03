"""Hybrid memory tools."""

from typing import Any, Dict, List, Optional, Callable, Awaitable
from autogen_core.components.tools._base import CancellationToken
from autogen_mem0.core.tools import BaseTool
from mem0 import Memory

from .models import (
    SemanticSearchInput,
    StoreMemoryInput,
    RecallMemoryInput,
    StoreMemoryOutput,
    RecallMemoryOutput
)

class HybridSearchTool(BaseTool):
    """Tool for hybrid search across both vector and graph stores."""

    def __init__(self, memory: Memory):
        if not (memory.config.vector_store and memory.config.graph_store):
            raise ValueError("Both vector and graph stores must be enabled for hybrid search")
            
        super().__init__(
            args_type=SemanticSearchInput,
            return_type=List[Dict[str, Any]],
            name="hybrid_search",
            description="Perform hybrid search across both vector and graph stores."
        )
        self.memory = memory

    async def run(self, args: SemanticSearchInput, cancellation_token: Optional[CancellationToken] = None) -> List[Dict[str, Any]]:
        """Perform hybrid search."""
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
            store_type="all",
            **filters
        )
        
        all_results = []
        if "vector" in results:
            all_results.extend(results["vector"])
        if "graph" in results:
            all_results.extend(results["graph"])
        return all_results

class FunctionBasedStoreTool(BaseTool):
    """Tool for storing memories using a custom store function."""

    def __init__(
            self,
            store_fn: Callable[[str, str, Optional[Dict[str, Any]], ...], Awaitable[Dict[str, Any]]]
        ):
        super().__init__(
            args_type=StoreMemoryInput,
            return_type=StoreMemoryOutput,
            name="custom_store_memory",
            description="Store information in memory using custom store function"
        )
        self.store_fn = store_fn

    async def run(self, args: StoreMemoryInput, cancellation_token: Optional[CancellationToken] = None) -> StoreMemoryOutput:
        """Store a memory using the custom store function."""
        filters = {}
        if args.user_id:
            filters["user_id"] = args.user_id
        if args.agent_id:
            filters["agent_id"] = args.agent_id
        if args.run_id:
            filters["run_id"] = args.run_id
        if args.filters:
            filters.update(args.filters)

        result = await self.store_fn(
            content=args.messages,
            store_type=args.store_type or "all",
            metadata=args.metadata,
            **filters
        )
        return StoreMemoryOutput(**result)

class FunctionBasedRecallTool(BaseTool):
    """Tool for recalling memories using a custom recall function."""

    def __init__(
            self,
            recall_fn: Callable[[str, str, int, ...], Awaitable[Dict[str, Any]]]
        ):
        super().__init__(
            args_type=RecallMemoryInput,
            return_type=RecallMemoryOutput,
            name="custom_recall_memory",
            description="Recall information from memory using custom recall function"
        )
        self.recall_fn = recall_fn

    async def run(self, args: RecallMemoryInput, cancellation_token: Optional[CancellationToken] = None) -> RecallMemoryOutput:
        """Recall memories using the custom recall function."""
        filters = {}
        if args.user_id:
            filters["user_id"] = args.user_id
        if args.agent_id:
            filters["agent_id"] = args.agent_id
        if args.run_id:
            filters["run_id"] = args.run_id
        if args.filters:
            filters.update(args.filters)

        result = await self.recall_fn(
            query=args.query,
            store_type=args.store_type or "all",
            limit=args.limit or 100,
            **filters
        )
        return RecallMemoryOutput(**result)