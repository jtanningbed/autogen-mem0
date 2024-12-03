"""Configuration schemas for Anthropic AutoGen."""

from typing import Dict, Optional, Any, Union
from pydantic import BaseModel, Field

from mem0.configs.base import MemoryConfig


class ModelConfig(BaseModel):
    """Model configuration."""
    max_tokens: Optional[int] = Field(
        default=None,
        description="Maximum number of tokens to generate"
    )
    temperature: Optional[float] = Field(
        default=None,
        description="Temperature for sampling"
    )
    top_p: Optional[float] = Field(
        default=None,
        description="Top-p sampling parameter"
    )
    top_k: Optional[int] = Field(
        default=None,
        description="Top-k sampling parameter"
    )
    extra: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional model-specific settings"
    )


class EnvironmentConfig(BaseModel):
    """Configuration for an environment."""
    memory: Optional[Dict[str, Any]] = None
    # Additional environment-specific settings can be added here


class GlobalConfig(BaseModel):
    """Global configuration."""
    environments: Dict[str, EnvironmentConfig] = Field(
        default_factory=dict,
        description="Environment configurations"
    )
    default_environment: str = Field(
        default="default",
        description="Default environment to use"
    )
