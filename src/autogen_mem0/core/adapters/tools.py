"""Tool adaptation layer."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic, Union, TYPE_CHECKING

from anthropic.types.beta import (
    BetaToolParam,
    BetaToolComputerUse20241022Param,
    BetaToolBash20241022Param,
    BetaToolTextEditor20241022Param,
)
from autogen_core.components.tools import FunctionTool, Tool, ToolSchema

if TYPE_CHECKING:
    from ..tools._base import BaseTool

T = TypeVar('T')
U = TypeVar('U')

class ToolAdapter(ABC, Generic[T, U]):
    """Base adapter interface for converting between tool types."""
    
    @abstractmethod
    def adapt(self, tool: T) -> U:
        """Convert from source type T to target type U."""
        pass

class AnthropicToolAdapter(ToolAdapter[Tool, Union[
    BetaToolParam,
    BetaToolComputerUse20241022Param,
    BetaToolBash20241022Param,
    BetaToolTextEditor20241022Param,
]]):
    """Converts our tools to Anthropic beta tool format."""

    def adapt(self, tools: List[Tool]) -> Union[
        BetaToolParam,
        BetaToolComputerUse20241022Param,
        BetaToolBash20241022Param,
        BetaToolTextEditor20241022Param,
    ]:
        """Convert our tool to appropriate Anthropic format."""
        anthropic_tools: List[BetaToolParam] = []
        for tool in tools:
            schema: ToolSchema = tool.schema

            # Special handling for computer-use tools
            tool_type = schema.get("type")
            if tool_type in ["computer_20241022", "text_editor_20241022", "bash_20241022"]:
                beta_param = {
                    "type": tool_type,
                    "name": schema["name"]
                }
                # Add any additional computer-use specific parameters
                for param in ["display_width_px", "display_height_px", "display_number"]:
                    if param in schema:
                        beta_param[param] = schema[param]

                # Return appropriate computer-use param type
                if tool_type == "computer_20241022":
                    anthropic_tools.append(
                        BetaToolComputerUse20241022Param(**beta_param)
                    )
                    continue
                elif tool_type == "text_editor_20241022":
                    anthropic_tools.append(
                        BetaToolTextEditor20241022Param(**beta_param)
                    )
                    continue
                elif tool_type =="bash_20241022": 
                    anthropic_tools.append(
                        BetaToolBash20241022Param(**beta_param)
                    )
                    continue
            else:
                anthropic_tool = BetaToolParam(
                    name=schema["name"],
                    description=schema.get("description", ""),
                    input_schema={
                        "type": "object",
                        "properties": schema.get("parameters", {}).get("properties", {}),
                        "required": schema.get("parameters", {}).get("required", []),
                    },
                )
                anthropic_tools.append(anthropic_tool)

        return anthropic_tools

class FunctionToolAdapter(ToolAdapter[Tool, FunctionTool]):
    """Converts our tools to autogen FunctionTool format for execution."""
    
    def adapt(self, tool: Tool) -> FunctionTool:
        """Convert our tool to FunctionTool format."""
        async def execute(params: Dict[str, Any]) -> Any:
            return await tool.run(tool._args_type(**params), None)

        return FunctionTool(
            func=execute,
            description=tool.description,
            name=tool.name
        )

class ToolAdapterFactory:
    """Factory for creating tool adapters."""
    
    _adapters: Dict[str, ToolAdapter] = {}
    
    @classmethod
    def register(cls, name: str, adapter: ToolAdapter):
        """Register a tool adapter."""
        cls._adapters[name] = adapter
    
    @classmethod
    def get_adapter(cls, name: str) -> Optional[ToolAdapter]:
        """Get adapter by name."""
        return cls._adapters.get(name)
    
    @classmethod
    def adapt_tools(cls, tools: Any, target_format: str) -> Any:
        """Adapt a tool to target format."""
        adapter = cls.get_adapter(target_format)
        if not adapter:
            raise ValueError(f"No adapter found for format: {target_format}")
        return adapter.adapt(tools)
