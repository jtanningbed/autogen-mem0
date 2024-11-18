"""
Base classes and interfaces for tools.
Provides compatibility with autogen tools while maintaining custom functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, Field

from autogen_core.components.tools import Tool
from autogen_core.base import CancellationToken


class ToolResult(BaseModel):
    """Result of a tool execution."""
    success: bool = Field(description="Whether the tool execution was successful")
    output: Any = Field(description="Output of the tool execution")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the execution"
    )

    def as_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata
        }


class BaseTool(Tool):
    """Base tool compatible with autogen while maintaining custom functionality."""

    def __init__(
        self,
        name: str,
        description: str,
        return_type: Type[BaseModel],
        **kwargs
    ):
        """Initialize tool."""
        self._name = name
        self._description = description
        self._return_type = return_type

    @property
    def name(self) -> str:
        """Name of the tool."""
        return self._name

    @property
    def description(self) -> str:
        """Description of what the tool does."""
        return self._description

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with the given parameters.
        
        This is our custom execution method that returns our ToolResult type.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            ToolResult: Result of the tool execution
        """
        pass

    async def run(self, args: BaseModel, cancellation_token: CancellationToken) -> BaseModel:
        """Autogen-compatible tool execution.
        
        This implements the autogen Tool interface while using our execute() method.
        
        Args:
            args: Tool parameters
            cancellation_token: Token for cancellation
            
        Returns:
            BaseModel: Result in autogen format
        """
        result = await self.execute(**args.model_dump())
        return self._return_type(**result.as_dict())

    def __str__(self) -> str:
        """String representation of the tool."""
        return f"{self.name}: {self.description}"
