"""Parameter adaptation layer for API clients."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic

from anthropic.types.beta import (
    BetaToolParam,
    BetaToolComputerUse20241022Param,
)

T = TypeVar('T')
U = TypeVar('U')

class ParameterAdapter(ABC, Generic[T, U]):
    """Base adapter interface for converting API parameters."""
    
    @abstractmethod
    def adapt(self, params: T) -> U:
        """Convert parameters from source format to target format."""
        pass

class AnthropicCreateParamAdapter(ParameterAdapter[Dict[str, Any], Dict[str, Any]]):
    """Adapts create() parameters for Anthropic API."""
    
    def adapt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Convert standard parameters to Anthropic format."""
        adapted = {
            "model": params.get("model"),
            "max_tokens": params.get("max_tokens", 1024),
            "messages": params.get("messages", [])
        }
        
        # Handle system message
        if "system" in params:
            adapted["system"] = params["system"]
            
        # Handle tools
        if "tools" in params:
            adapted["tools"] = params["tools"]
            adapted["tool_choice"] = {"type": "auto"}
            
        return adapted

class ParameterAdapterFactory:
    """Factory for creating parameter adapters."""
    
    _adapters: Dict[str, ParameterAdapter] = {}
    
    @classmethod
    def register(cls, name: str, adapter: ParameterAdapter):
        """Register a parameter adapter."""
        cls._adapters[name] = adapter
    
    @classmethod
    def get_adapter(cls, name: str) -> Optional[ParameterAdapter]:
        """Get adapter by name."""
        return cls._adapters.get(name)

# Register default adapters
ParameterAdapterFactory.register(
    "anthropic.create",
    AnthropicCreateParamAdapter()
)
