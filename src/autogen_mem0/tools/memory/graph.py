"""Graph memory tools."""

from typing import Any, Dict, List, Optional
from autogen_core.components.tools._base import CancellationToken
from autogen_mem0.core.tools import BaseTool
from mem0 import Memory

from .models import GetRelatedEntitiesInput

class GraphSearchTool(BaseTool):
    """Tool for searching entities in graph memory."""

    def __init__(self, memory: Memory):
        if not memory.config.graph_store and not memory.config.graph_store.config:
            raise ValueError("Graph store is not enabled")
            
        super().__init__(
            args_type=GetRelatedEntitiesInput,
            return_type=List[Dict[str, Any]],
            name="graph_search",
            description="Search for nodes and relations in the graph store."
        )
        self.memory = memory

    async def run(self, args: GetRelatedEntitiesInput, cancellation_token: Optional[CancellationToken] = None) -> List[Dict[str, Any]]:
        """Search graph store."""
        filters = {}
        if args.user_id:
            filters["user_id"] = args.user_id
        if args.agent_id:
            filters["agent_id"] = args.agent_id
        if args.run_id:
            filters["run_id"] = args.run_id

        return await self.memory.get_related_entities(
            entity=args.entity,
            relationship_type=args.relationship_type,
            store_type="graph",
            **filters
        )

class GetRelatedEntitiesTool(BaseTool):
    """Tool for finding related entities in graph memory."""

    def __init__(self, memory: Memory):
        if not memory.config.graph_store and not memory.config.graph_store.config:
            raise ValueError("Graph store is not enabled")
            
        super().__init__(
            args_type=GetRelatedEntitiesInput,
            return_type=List[Dict[str, Any]],
            name="get_related_entities",
            description="Find entities related to a given entity"
        )
        self.memory = memory

    async def run(self, args: GetRelatedEntitiesInput, cancellation_token: Optional[CancellationToken] = None) -> List[Dict[str, Any]]:
        """Get related entities."""
        filters = {}
        if args.user_id:
            filters["user_id"] = args.user_id
        if args.agent_id:
            filters["agent_id"] = args.agent_id
        if args.run_id:
            filters["run_id"] = args.run_id

        return await self.memory.get_related_entities(
            entity=args.entity,
            relationship_type=args.relationship_type,
            **filters
        )