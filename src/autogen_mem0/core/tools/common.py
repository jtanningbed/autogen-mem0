"""Common tool implementations for autogen-mem0."""

from typing import Any, Dict, List, Optional, Callable, Awaitable, Union
from pydantic import BaseModel, Field
from autogen_mem0.core.tools._base import BaseTool 
from autogen_core.components.tools._base import CancellationToken

from mem0 import Memory
from mem0.configs.base import MemoryConfig
import json

# Input/Output Models
class Entity(BaseModel):
    """Entity in a graph relationship."""
    source_node: str = Field(description="The identifier of the source node")
    source_type: str = Field(description="The type or category of the source node")
    relation: str = Field(description="The type of relationship between nodes")
    destination_node: str = Field(description="The identifier of the destination node")
    destination_type: str = Field(description="The type or category of the destination node")

class StoreMemoryInput(BaseModel):
    """Input for storing a memory."""
    messages: Union[str, List[Dict[str, str]]] = Field(description="Content to store in memory. Can be a string or a list of message dicts with 'role' and 'content' keys")
    metadata: Optional[Dict[str, Any]] = Field(description="Additional metadata to store", default=None)
    user_id: Optional[str] = Field(description="User ID associated with memory", default=None)
    agent_id: Optional[str] = Field(description="Agent ID associated with memory", default=None)
    run_id: Optional[str] = Field(description="Run ID associated with memory", default=None)
    filters: Optional[Dict[str, Any]] = Field(description="Additional filters for storage", default=None)

class StoreRelationshipInput(BaseModel):
    """Input for storing a relationship in graph memory."""
    source: str = Field(
        description="The identifier of the source node in the new relationship. This can be an existing node or a new node to be created."
    )
    destination: str = Field(
        description="The identifier of the destination node in the new relationship. This can be an existing node or a new node to be created."
    )
    relationship: str = Field(
        description="The type of relationship between the source and destination nodes. This should be a concise, clear description of how the two nodes are connected."
    )
    source_type: str = Field(
        description="The type or category of the source node. This helps in classifying and organizing nodes in the graph."
    )
    destination_type: str = Field(
        description="The type or category of the destination node. This helps in classifying and organizing nodes in the graph."
    )
    user_id: Optional[str] = Field(description="User ID associated with memory", default=None)
    agent_id: Optional[str] = Field(description="Agent ID associated with memory", default=None)
    run_id: Optional[str] = Field(description="Run ID associated with memory", default=None)

class UpdateRelationshipInput(BaseModel):
    """Input for updating a relationship in graph memory."""
    source: str = Field(
        description="The identifier of the source node in the relationship to be updated. This should match an existing node in the graph."
    )
    destination: str = Field(
        description="The identifier of the destination node in the relationship to be updated. This should match an existing node in the graph."
    )
    relationship: str = Field(
        description="The new or updated relationship between the source and destination nodes. This should be a concise, clear description of how the two nodes are connected."
    )
    user_id: Optional[str] = Field(description="User ID associated with memory", default=None)
    agent_id: Optional[str] = Field(description="Agent ID associated with memory", default=None)
    run_id: Optional[str] = Field(description="Run ID associated with memory", default=None)

class GetRelatedEntitiesInput(BaseModel):
    """Input for finding related entities in graph memory."""
    entity: str = Field(description="Entity to find relationships for")
    relationship_type: Optional[str] = Field(description="Type of relationship to filter by", default=None)
    user_id: Optional[str] = Field(description="User ID associated with memory", default=None)
    agent_id: Optional[str] = Field(description="Agent ID associated with memory", default=None)
    run_id: Optional[str] = Field(description="Run ID associated with memory", default=None)

class SemanticSearchInput(BaseModel):
    """Input for semantic search."""
    query: str = Field(description="Query to search for")
    limit: Optional[int] = Field(description="Maximum number of results to return", default=10)
    user_id: Optional[str] = Field(description="User ID associated with memory", default=None)
    agent_id: Optional[str] = Field(description="Agent ID associated with memory", default=None)
    run_id: Optional[str] = Field(description="Run ID associated with memory", default=None)

class RecallMemoryInput(BaseModel):
    """Input for recalling memories."""
    query: str = Field(description="Query to search for")
    limit: Optional[int] = Field(description="Maximum number of results to return", default=10)
    user_id: Optional[str] = Field(description="User ID associated with memory", default=None)
    agent_id: Optional[str] = Field(description="Agent ID associated with memory", default=None)
    run_id: Optional[str] = Field(description="Run ID associated with memory", default=None)
    filters: Optional[Dict[str, Any]] = Field(description="Additional filters for recall. These narrow the search scope to memory items that were stored with specific metadata", default=None)

class StoreMemoryOutput(BaseModel):
    """Output from storing a memory."""
    # id: str = Field(description="ID of stored memory")
    # content: Any = Field(description="Stored content")
    # metadata: Optional[Dict[str, Any]] = Field(description="Associated metadata", default=None)
    results: Optional[Any] = Field(description="Results from vector store", default=None)
    relations: Optional[Any] = Field(description="Results from graph store", default=None)

class RecallMemoryOutput(BaseModel):
    """Output from recalling memories."""
    results: Any = Field(
        description="Results from vector store"
    )
    relations: Optional[Any] = Field(
        description="Results from graph store", default=None
    )

# Tool Implementations
class StoreMemoryTool(BaseTool):
    """Tool for storing memories."""
    
    def __init__(self, memory: Memory):
        super().__init__(
            args_type=StoreMemoryInput,
            return_type=StoreMemoryOutput,
            name="store_memory",
            description="Store information in memory for later retrieval"
        )
        self.memory = memory

    async def run(self, args: StoreMemoryInput, cancellation_token: Optional[CancellationToken] = None) -> StoreMemoryOutput:
        """Store memory with context."""
        # Get context from args
        context = {}
        if args.metadata:
            context.update(args.metadata)
            
        user_id = args.user_id
        agent_id = args.agent_id
        run_id = args.run_id

        if not any([user_id, agent_id, run_id]):
            raise ValueError("At least one of user_id, agent_id, or run_id must be provided in context or args")

        # Store memory with context
        try:
            result = self.memory.add(
                messages=args.messages,
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id,
                metadata=context
            )
            
            # Handle both v1.1 and legacy formats
            if isinstance(result, dict):
                return StoreMemoryOutput(
                    results=result.get("results", []),
                    relations=result.get("relations")
                )
            else:
                # Legacy format returns just the results
                return StoreMemoryOutput(results=result)
                
        except Exception as e:
            raise ValueError(f"Failed to store memory: {str(e)}")

class StoreRelationshipTool(BaseTool):
    """Tool for storing relationships in graph memory."""

    def __init__(self, memory: Memory):
        if not memory.config.graph_store and not memory.config.graph_store.config:
            raise ValueError("Graph store is not enabled")
            
        super().__init__(
            args_type=StoreRelationshipInput,
            return_type=StoreMemoryOutput,
            name="add_graph_memory",
            description="Add a new graph memory to the knowledge graph. This function creates a new relationship between two nodes, potentially creating new nodes if they don't exist."
        )
        self.memory = memory

    async def run(self, args: StoreRelationshipInput, cancellation_token: Optional[CancellationToken] = None) -> StoreMemoryOutput:
        """Store a relationship."""
        filters = {}
        if args.user_id:
            filters["user_id"] = args.user_id
        if args.agent_id:
            filters["agent_id"] = args.agent_id
        if args.run_id:
            filters["run_id"] = args.run_id

        result = await self.memory.graph.add({
            "source": args.source,
            "source_type": args.source_type,
            "relationship": args.relationship,
            "destination": args.destination,
            "destination_type": args.destination_type
        }, filters=filters)
        return StoreMemoryOutput(**result)

class UpdateRelationshipTool(BaseTool):
    """Tool for updating relationships in graph memory."""

    def __init__(self, memory: Memory):
        if not memory.config.graph_store and not memory.config.graph_store.config:
            raise ValueError("Graph store is not enabled")
            
        super().__init__(
            args_type=UpdateRelationshipInput,
            return_type=StoreMemoryOutput,
            name="update_graph_memory",
            description="Update the relationship key of an existing graph memory based on new information. This function should be called when there's a need to modify an existing relationship in the knowledge graph. The update should only be performed if the new information is more recent, more accurate, or provides additional context compared to the existing information. The source and destination nodes of the relationship must remain the same as in the existing graph memory; only the relationship itself can be updated."
        )
        self.memory = memory

    async def run(self, args: UpdateRelationshipInput, cancellation_token: Optional[CancellationToken] = None) -> StoreMemoryOutput:
        """Update a relationship."""
        filters = {}
        if args.user_id:
            filters["user_id"] = args.user_id
        if args.agent_id:
            filters["agent_id"] = args.agent_id
        if args.run_id:
            filters["run_id"] = args.run_id

        result = await self.memory.graph.update({
            "source": args.source,
            "destination": args.destination,
            "relationship": args.relationship
        }, filters=filters)
        return StoreMemoryOutput(**result)

class GetRelatedEntitiesTool(BaseTool):
    """Tool for finding related entities in graph memory."""

    def __init__(self, memory: Memory):
        if not memory.config.graph_store and not memory.config.graph_store.config:
            raise ValueError("Graph store is not enabled")
            
        super().__init__(
            args_type=GetRelatedEntitiesInput,
            return_type=List[Dict[str, Any]],
            name="get_related_entities",
            description="Search for nodes and relations in the graph."
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

class SemanticSearchTool(BaseTool):
    """Tool for semantic search in vector memory."""

    def __init__(self, memory: Memory):
        if not memory.config.vector_store and not memory.config.vector_store.config:
            raise ValueError("Vector store is not configured")
            
        super().__init__(
            args_type=SemanticSearchInput,
            return_type=Dict[str, Any],
            name="semantic_search",
            description="Search memories by semantic similarity"
        )
        self.memory = memory

    async def run(self, args: SemanticSearchInput, cancellation_token: Optional[CancellationToken] = None) -> Dict[str, Any]:
        """Search for memories."""
        filters = {}
        if args.user_id:
            filters["user_id"] = args.user_id
        if args.agent_id:
            filters["agent_id"] = args.agent_id
        if args.run_id:
            filters["run_id"] = args.run_id

        return await self.memory.recall(
            query=args.query,
            store_type="vector",
            limit=args.limit,
            **filters
        )

class RecallMemoryTool(BaseTool):
    """Tool for recalling memories."""
    
    def __init__(self, memory: Memory):
        super().__init__(
            args_type=RecallMemoryInput,
            return_type=RecallMemoryOutput,
            name="recall_memory",
            description="Recall previously stored information from memory. Note: Context will be automatically provided from the client."
        )
        self.memory = memory

    async def run(self, args: RecallMemoryInput, cancellation_token: Optional[CancellationToken] = None) -> RecallMemoryOutput:
        """Recall memories with context."""
        user_id = args.user_id
        agent_id = args.agent_id
        run_id = args.run_id
        
        if not any([user_id, agent_id, run_id]):
            raise ValueError("At least one of user_id, agent_id, or run_id must be provided")
            
        try:
            # Search with top-level parameters and optional metadata filters
            results = self.memory.search(
                query=args.query,
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id,
                limit=args.limit or 10,
                filters=args.filters  # Optional metadata filters like {"topic": "geography"}
            )
            
            # Handle both v1.1 and legacy formats
            if isinstance(results, dict):
                return RecallMemoryOutput(
                    results=results.get("results", []),
                    relations=results.get("relations")
                )
            else:
                # Legacy format returns just the results list
                return RecallMemoryOutput(results=results)
                
        except Exception as e:
            raise ValueError(f"Failed to recall memories: {str(e)}")

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
            store_type="graph",  # Explicitly use graph store
            **filters
        )

class VectorSearchTool(BaseTool):
    """Tool for semantic search in vector memory."""

    def __init__(self, memory: Memory):
        if not memory.config.vector_store and not memory.config.vector_store.config:
            raise ValueError("Vector store is not enabled")
            
        super().__init__(
            args_type=SemanticSearchInput,  # Reuse existing input model
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
            store_type="vector",  # Explicitly use vector store
            **filters
        )
        return results.get("vector", [])

class HybridSearchTool(BaseTool):
    """Tool for hybrid search across both vector and graph stores."""

    def __init__(self, memory: Memory):
        if not (memory.config.vector_store and memory.config.graph_store):
            raise ValueError("Both vector and graph stores must be enabled for hybrid search")
            
        super().__init__(
            args_type=SemanticSearchInput,  # Reuse semantic search input
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
            store_type="all",  # Use both stores
            **filters
        )
        # Combine and deduplicate results
        all_results = []
        if "vector" in results:
            all_results.extend(results["vector"])
        if "graph" in results:
            all_results.extend(results["graph"])
        # Could add result ranking/scoring here
        return all_results

def create_memory_tools(
    store_fn: Callable[[str, str, Optional[Dict[str, Any]], ...], Awaitable[Dict[str, Any]]],
    recall_fn: Callable[[str, str, int, ...], Awaitable[Dict[str, Any]]]
) -> List[BaseTool]:
    """Create memory tools with custom store/recall functions.
    
    This is a simpler alternative to get_memory_tools() when you just need basic
    store/recall functionality with custom functions, without needing a full MemoryManager.
    Useful for wrapping memory operations with additional context or preprocessing.
    
    Args:
        store_fn: Async function for storing memories with unified interface:
            content: Content to store
            store_type: Which store to use ("all", "vector", "graph")
            metadata: Optional metadata to store
            **kwargs: Additional arguments
            Returns: Dict containing results from specified stores
            
        recall_fn: Async function for recalling memories with unified interface:
            query: Search query
            store_type: Which store to search ("all", "vector", "graph")
            limit: Max number of results
            **kwargs: Additional arguments
            Returns: Dict containing results from specified stores
        
    Returns:
        List containing FunctionBasedStoreTool and FunctionBasedRecallTool configured with the custom functions
        
    Example:
        ```python
        async def store_with_context(
            content: str,
            store_type: str = "all",
            metadata: Optional[Dict] = None,
            **kwargs
        ) -> Dict[str, Any]:
            # Add context before storing
            context = {"conversation_id": "123", "speaker": "user"}
            metadata = {**(metadata or {}), **context}
            return await memory_manager.store(content, store_type, metadata, **kwargs)
            
        async def recall_with_context(
            query: str,
            store_type: str = "all",
            limit: int = 100,
            **kwargs
        ) -> Dict[str, Any]:
            # Add context before recall
            context = {"conversation_id": "123"}
            kwargs["filters"] = {**(kwargs.get("filters", {})), **context}
            return await memory_manager.recall(query, store_type, limit, **kwargs)
            
        tools = create_memory_tools(store_with_context, recall_with_context)
        ```
    """
    return [
        FunctionBasedStoreTool(store_fn),
        FunctionBasedRecallTool(recall_fn)
    ]

def get_memory_tools(memory: Memory) -> List[BaseTool]:
    """Get all available memory tools based on configuration."""
    tools = [
        StoreMemoryTool(memory),
        RecallMemoryTool(memory)
    ]

    # Check if graph store is actually configured
    if memory.config.graph_store and memory.config.graph_store.config:
        tools.extend([
            StoreRelationshipTool(memory),
            UpdateRelationshipTool(memory),
            GetRelatedEntitiesTool(memory),
            GraphSearchTool(memory)
        ])

    # Check if vector store is actually configured
    if memory.config.vector_store and memory.config.vector_store.config:
        tools.append(SemanticSearchTool(memory))
        tools.append(VectorSearchTool(memory))

    # Check if both vector and graph stores are configured
    if memory.config.vector_store and memory.config.graph_store and memory.config.vector_store.config and memory.config.graph_store.config:
        tools.append(HybridSearchTool(memory))

    return tools