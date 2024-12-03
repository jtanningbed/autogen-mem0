"""Context management tools."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from autogen_core.base import CancellationToken
from autogen_mem0.core.tools._base import BaseTool

class EntityContext(BaseModel):
    """Context about an entity being discussed."""
    name: str = Field(description="Name or identifier of the entity")
    type: str = Field(description="Type of entity (person, location, concept, etc)")
    relationship_to_user: Optional[str] = Field(
        description="How this entity relates to the user (friend, family, colleague, etc)",
        default=None
    )
    attributes: Optional[Dict[str, Any]] = Field(
        description="Additional attributes about the entity",
        default=None
    )

class ConversationContext(BaseModel):
    """Current context of the conversation."""
    primary_subject: Optional[EntityContext] = Field(
        description="The main entity being discussed",
        default=None
    )
    related_entities: Optional[List[EntityContext]] = Field(
        description="Other entities mentioned in relation to the primary subject",
        default=None
    )
    temporal_context: Optional[Dict[str, Any]] = Field(
        description="Time-related context (past events, future plans, etc)",
        default=None
    )
    spatial_context: Optional[Dict[str, Any]] = Field(
        description="Location or space-related context",
        default=None
    )
    topic_context: Optional[Dict[str, Any]] = Field(
        description="Subject matter or topic being discussed",
        default=None
    )

class GetContextInput(BaseModel):
    """Input for getting conversation context."""
    conversation_id: Optional[str] = Field(description="Conversation ID to get context for", default=None)

class GetContextOutput(BaseModel):
    """Output containing context information."""
    agent_id: Optional[str] = Field(
        description="Agent ID associated with current context",
        default=None
    )
    user_id: Optional[str] = Field(
        description="User ID associated with current context",
        default=None
    )
    session_id: Optional[str] = Field(
        description="Session/Run ID associated with current context",
        default=None
    )
    conversation_context: Optional[ConversationContext] = Field(
        description="Rich context about the current conversation state",
        default=None
    )
    metadata: Optional[Dict[str, Any]] = Field(
        description="Additional context metadata",
        default=None
    )

class GetContextTool(BaseTool[GetContextInput, GetContextOutput]):
    """Tool for getting conversation context."""
    
    def __init__(self):
        """Initialize the get context tool."""
        super().__init__(
            args_type=GetContextInput,
            return_type=GetContextOutput,
            name="get_context",
            description="""
            Get the current conversation context including:
            - Identity information (user_id, agent_id)
            - Rich conversation context (who/what is being discussed)
            - Related entities and relationships
            - Temporal and spatial context
            - Topic and theme information
            
            Use this to understand the current state of conversation and maintain continuity.
            """
        )
        self._context = GetContextOutput()

    async def run(
        self,
        args: GetContextInput,
        cancellation_token: Optional[CancellationToken] = None
    ) -> GetContextOutput:
        """Get current context."""
        return self._context

def get_context_tools() -> list[BaseTool]:
    """Get context management tools."""
    get_tool = GetContextTool()
    return [get_tool]
