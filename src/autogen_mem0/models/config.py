"""Configuration classes for Anthropic clients."""

from typing import Optional, Union
from typing_extensions import TypedDict

from autogen_core.components.models import ModelCapabilities
from autogen_core.components.models.config import CreateArguments


class BaseAnthropicClientConfiguration(CreateArguments, total=False):
    """Base configuration for Anthropic clients."""
    model: str
    api_key: str
    timeout: Union[float, None]
    max_retries: int
    max_tokens: Optional[int]
    temperature: Optional[float]
    top_p: Optional[float]
    top_k: Optional[int]
    stream: Optional[bool]


class AnthropicClientConfiguration(BaseAnthropicClientConfiguration, total=False):
    """Configuration for Anthropic clients with additional options."""
    base_url: str  # For custom endpoints
    model_capabilities: ModelCapabilities  # Optional model capabilities
    version: str  # API version
    anthropic_version: str  # Anthropic-Version header value
