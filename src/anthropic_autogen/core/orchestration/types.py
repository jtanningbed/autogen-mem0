from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

class OrchestrationRequest(BaseModel):
    """Request for orchestration"""
    type: Literal["agent", "tool", "workflow"]
    action: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)

class OrchestrationResult(BaseModel):
    """Result of orchestration"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
