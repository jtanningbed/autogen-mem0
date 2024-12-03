"""Base tool implementation for autogen-mem0."""

from abc import ABC
from typing import Dict, Any, Optional, Type, TypeVar, Generic, Union, Sequence, Mapping, List
from autogen_core.components.tools import BaseTool as AutogenBaseTool, FunctionTool, ParametersSchema, ToolSchema
from autogen_core.base import CancellationToken
from anthropic.types.beta import (
    BetaToolParam,
    BetaToolComputerUse20241022Param,
    BetaToolBash20241022Param,
    BetaToolTextEditor20241022Param,
)
from pydantic import BaseModel, create_model
from typing import TypedDict, NotRequired
import json

from ..adapters.tools import ToolAdapterFactory

ArgsT = TypeVar("ArgsT", bound=BaseModel)
ReturnT = TypeVar("ReturnT")


class BaseTool(AutogenBaseTool[ArgsT, ReturnT], ABC):
    """Base class for all tools in autogen-mem0.
    
    This extends autogen's BaseTool with:
    1. Anthropic beta tool parameter support via to_beta_param()
    2. Support for computer-use tools
    3. Schema-based initialization
    4. Automatic input validation and serialization handling
    """

    def __init__(
        self,
        *,
        args_type: Type[BaseModel],
        return_type: Type[BaseModel] | Type[List[Dict[str, Any]]],
        name: str,
        description: str,
    ):
        """Initialize the tool.

        Args:
            args_type: The type of the arguments.
            return_type: The type of the return value.
            name: The name of the tool.
            description: A description of what the tool does.
        """
        self._args_type = args_type
        self._return_type = return_type
        self._name = name
        self._description = description

    @property
    def name(self) -> str:
        """Get tool name."""
        return self._name

    @property
    def description(self) -> str:
        """Get tool description."""
        return self._description

    @property 
    def schema(self) -> Dict[str, Any]:
        """Get tool schema.
        
        Returns original schema if tool was created from schema,
        otherwise generates schema from type information.
        """
        if hasattr(self, '_schema'):
            return self._schema
        return super().schema

    def adapt(self, adapter_name: str): 
        adapter = ToolAdapterFactory.get_adapter(adapter_name)
        if adapter:
            return adapter.adapt(self)
        else:
            raise ValueError(f"No adapter found for {adapter_name}")

    async def run_json(
        self, args: Mapping[str, Any], cancellation_token: CancellationToken
    ) -> Any:
        """Run the tool with proper input validation.

        This extends the base run_json to handle both dict and string inputs.
        """
        try:
            # Handle both dict and string inputs
            if isinstance(args, dict):
                validated_args = self._args_type.model_validate(args)
            elif isinstance(args, str):
                validated_args = self._args_type.model_validate(json.loads(args))
            else:
                raise ValueError(f"Expected dict or str args, got {type(args)}")

            return_value = await self.run(validated_args, cancellation_token)
            return return_value

        except Exception as e:
            print(f"Error in {self.__class__.__name__}: {e}")
            print(f"Args type: {type(args)}")
            print(f"Args content: {args}")
            raise

    def to_function_tool(self) -> FunctionTool:
        """Convert this tool to a FunctionTool for compatibility.
        
        This allows the tool to be used in contexts that expect FunctionTool's interface.
        The resulting FunctionTool will delegate actual execution to this tool's run() method.
        """
        return self.adapt("function")
