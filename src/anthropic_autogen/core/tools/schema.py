from typing import Any, Optional, Dict, List, TypeVar, Generic
from pydantic import BaseModel, Field

class ToolParameter(BaseModel):
    """Schema for a tool parameter"""
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None
    items: Optional[Dict[str, Any]] = None  # For array types
    properties: Optional[Dict[str, Any]] = None  # For object types
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ToolSchema(BaseModel):
    """Schema definition for a tool"""
    name: str
    description: str
    parameters: Dict[str, ToolParameter]
    version: str = "1.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)

T = TypeVar('T')

class ToolResponse(BaseModel, Generic[T]):
    """Response from a tool execution"""
    success: bool
    result: T
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
