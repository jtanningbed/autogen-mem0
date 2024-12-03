"""Base tool protocol implementation."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, Type, TypeVar
from pydantic import BaseModel
from autogen_core.components.tools._base import CancellationToken

InputType = TypeVar('InputType', bound=BaseModel)
OutputType = TypeVar('OutputType', bound=BaseModel)

class BaseTool(Generic[InputType, OutputType], ABC):
    """Base class for all tools.
    
    Tools should inherit from this class and implement the run() method.
    Input and output types should be Pydantic models.
    
    Example:
        ```python
        class MyTool(BaseTool[MyInput, MyOutput]):
            def __init__(self):
                super().__init__(
                    name="my_tool",
                    description="My tool description"
                )
                
            async def run(
                self,
                args: MyInput,
                cancellation_token: Optional[CancellationToken] = None
            ) -> MyOutput:
                # Tool implementation
                pass
        ```
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        args_type: Type[InputType],
        return_type: Type[OutputType],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize tool.
        
        Args:
            name: Tool name
            description: Tool description
            args_type: Input type (Pydantic model)
            return_type: Output type (Pydantic model)
            metadata: Optional metadata
        """
        self.name = name
        self.description = description
        self.args_type = args_type
        self.return_type = return_type
        self.metadata = metadata or {}
        self.schema = self._build_schema()
        
    def _build_schema(self) -> Dict[str, Any]:
        """Build JSON schema for tool.
        
        Returns:
            Dict containing tool schema
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.args_type.schema(),
            "returns": self.return_type.schema(),
            "metadata": self.metadata
        }
        
    @abstractmethod
    async def run(
        self,
        args: InputType,
        cancellation_token: Optional[CancellationToken] = None
    ) -> OutputType:
        """Execute the tool.
        
        Args:
            args: Input arguments (instance of args_type)
            cancellation_token: Optional token for cancellation
            
        Returns:
            Tool output (instance of return_type)
            
        Raises:
            ValueError: If inputs are invalid
            Exception: For tool-specific errors
        """
        pass