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
