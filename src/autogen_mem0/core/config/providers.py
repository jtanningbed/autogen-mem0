"""Provider-specific configuration handling."""

from typing import Dict, Optional, Any, Type
from pydantic import BaseModel

from ...models._model_info import (
    resolve_model,
    get_capabilities,
    get_token_limit,
    get_max_output_tokens,
    get_model_pricing,
)


class ProviderInfo(BaseModel):
    """Base class for provider information."""
    provider: str
    capabilities: Dict[str, Any]

    def to_config(self) -> Dict[str, Any]:
        """Convert to provider-specific configuration."""
        raise NotImplementedError


class AnthropicModelInfo(ProviderInfo):
    """Anthropic model information."""
    provider: str = "anthropic"
    model_alias: str
    resolved_model: str
    capabilities: Dict[str, bool]
    token_limit: int
    max_output_tokens: int
    pricing: Dict[str, float]

    @classmethod
    def from_alias(cls, model_alias: str) -> "AnthropicModelInfo":
        """Create model info from alias."""
        resolved = resolve_model(model_alias)
        return cls(
            model_alias=model_alias,
            resolved_model=resolved,
            capabilities=get_capabilities(resolved),
            token_limit=get_token_limit(resolved),
            max_output_tokens=get_max_output_tokens(resolved),
            pricing=get_model_pricing(resolved),
        )

    def to_config(self) -> Dict[str, Any]:
        """Convert to configuration dict."""
        return {
            "provider": self.provider,
            "model": self.resolved_model,
            "max_tokens": self.max_output_tokens,
            "extra": {
                "token_limit": self.token_limit,
                "capabilities": self.capabilities,
                "pricing": self.pricing,
            }
        }


class OpenAIModelInfo(ProviderInfo):
    """OpenAI model information."""
    provider: str = "openai"
    model: str
    capabilities: Dict[str, bool] = {
        "embeddings": True,
    }

    def to_config(self) -> Dict[str, Any]:
        """Convert to configuration dict."""
        return {
            "provider": self.provider,
            "model": self.model,
            "extra": {
                "capabilities": self.capabilities,
            }
        }


class OllamaModelInfo(ProviderInfo):
    """Ollama model information."""
    provider: str = "ollama"
    model: str
    capabilities: Dict[str, bool] = {
        "local": True,
        "embeddings": True,
    }

    def to_config(self) -> Dict[str, Any]:
        """Convert to configuration dict."""
        return {
            "provider": self.provider,
            "model": self.model,
            "extra": {
                "capabilities": self.capabilities,
            }
        }


# Registry of provider-specific model info classes
MODEL_INFO_REGISTRY: Dict[str, Type[ProviderInfo]] = {
    "anthropic": AnthropicModelInfo,
    "openai": OpenAIModelInfo,
    "ollama": OllamaModelInfo,
}
