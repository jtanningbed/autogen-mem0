from typing import Dict, Type, Optional
from .base import BaseTool

class ToolRegistry:
    """Central registry for all available tools"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools: Dict[str, Type[BaseTool]] = {}
        return cls._instance
    
    def register(self, tool_class: Type[BaseTool]) -> None:
        """Register a tool class"""
        tool = tool_class()
        self._tools[tool.name] = tool_class
        
    def get_tool(self, name: str) -> Optional[Type[BaseTool]]:
        """Get a tool class by name"""
        return self._tools.get(name)
        
    def list_tools(self) -> Dict[str, Type[BaseTool]]:
        """List all registered tools"""
        return self._tools.copy()

# Global registry instance
registry = ToolRegistry()
