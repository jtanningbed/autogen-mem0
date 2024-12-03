"""Memory tool utilities."""

from typing import Any, Dict, List, Optional, Callable, Awaitable
from mem0 import Memory
from autogen_mem0.core.tools import BaseTool

from .store import StoreMemoryTool, StoreRelationshipTool, UpdateRelationshipTool
from .recall import RecallMemoryTool, SemanticSearchTool
from .graph import GraphSearchTool, GetRelatedEntitiesTool
from .vector import VectorSearchTool
from .hybrid import HybridSearchTool, FunctionBasedStoreTool, FunctionBasedRecallTool

def create_memory_tools(
    store_fn: Callable[[str, str, Optional[Dict[str, Any]], ...], Awaitable[Dict[str, Any]]],
    recall_fn: Callable[[str, str, int, ...], Awaitable[Dict[str, Any]]]
) -> List[BaseTool]:
    """Create memory tools with custom store/recall functions.
    
    Args:
        store_fn: Async function for storing memories
        recall_fn: Async function for recalling memories
        
    Returns:
        List containing FunctionBasedStoreTool and FunctionBasedRecallTool
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

    if memory.config.graph_store and memory.config.graph_store.config:
        tools.extend([
            StoreRelationshipTool(memory),
            UpdateRelationshipTool(memory),
            GetRelatedEntitiesTool(memory),
            GraphSearchTool(memory)
        ])

    if memory.config.vector_store and memory.config.vector_store.config:
        tools.append(VectorSearchTool(memory))

    if memory.config.vector_store and memory.config.graph_store:
        if memory.config.vector_store.config and memory.config.graph_store.config:
            tools.append(HybridSearchTool(memory))

    return tools