"""Base configuration management for Anthropic AutoGen."""

import os
from pathlib import Path
from typing import Dict, Optional, Any, Union

import yaml
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from mem0.configs.base import (
    MemoryConfig,
    VectorStoreConfig,
    EmbedderConfig,
    LlmConfig,
    GraphStoreConfig,
)

from ...models._model_info import (
    get_capabilities,
    get_token_limit,
    get_max_output_tokens,
    get_model_pricing,
)


def _resolve_env_vars(value: str) -> str:
    """Resolve environment variables in string values."""
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        env_var = value[2:-1]
        # Load from .env file first
        load_dotenv()
        env_value = os.getenv(env_var)
        if not env_value:
            raise ValueError(f"Environment variable {env_var} not found in .env file")
        return env_value
    return value


def _process_config_values(config: Dict) -> Dict:
    """Process configuration values, resolving environment variables."""
    processed = {}
    for key, value in config.items():
        if isinstance(value, dict):
            processed[key] = _process_config_values(value)
        else:
            processed[key] = _resolve_env_vars(value)
    return processed


class ConfigurationBase:
    """Base class for configuration management."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize configuration with optional custom directory."""
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Default to repo config directory
            self.config_dir = Path(__file__).parent.parent.parent.parent.parent / "config"
            
    def _load_yaml(self, filename: str, default: Dict = None) -> Dict:
        """Load and process a YAML configuration file."""
        config_path = self.config_dir / filename
        if not config_path.exists():
            return default or {}
            
        with open(config_path) as f:
            configs = yaml.safe_load(f)
            return _process_config_values(configs)


class VectorStoreConfiguration(ConfigurationBase):
    """Vector store configuration management."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize vector store configuration."""
        super().__init__(config_dir)
        self.configs = self._load_yaml("memory/vector_store.yaml", {"default": {}})
        
    def get_config(self, env: str = "default") -> Dict:
        """Get vector store configuration for environment."""
        return self.configs.get(env, self.configs.get("default", {}))
        
    def to_mem0_config(self, env: str = "default") -> VectorStoreConfig:
        """Convert to mem0 VectorStoreConfig."""
        config = self.get_config(env)
        return VectorStoreConfig(
            provider=config.get("store_type", "chroma"),
            config=config.get("store_settings", {})
        )


class ModelConfiguration(ConfigurationBase):
    """Model configuration management."""
    
    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """Get configuration for a specific model."""
        return {
            "capabilities": get_capabilities(model_name),
            "token_limit": get_token_limit(model_name),
            "max_output_tokens": get_max_output_tokens(model_name),
            "pricing": get_model_pricing(model_name),
        }
        
    def to_mem0_config(self, model_name: str) -> LlmConfig:
        """Convert to mem0 LlmConfig."""
        return LlmConfig(
            provider="anthropic",
            config={"model": model_name}
        )


class EmbedderConfiguration(ConfigurationBase):
    """Embedder configuration management."""
    
    def to_mem0_config(self, provider: str = "openai", **kwargs) -> EmbedderConfig:
        """Convert to mem0 EmbedderConfig."""
        return EmbedderConfig(
            provider=provider,
            config=kwargs
        )


class MemoryConfiguration:
    """Memory system configuration management."""
    
    def __init__(
        self,
        config_dir: Optional[str] = None,
        env: str = "default"
    ):
        """Initialize memory configuration."""
        self.vector_store = VectorStoreConfiguration(config_dir)
        self.model = ModelConfiguration(config_dir)
        self.embedder = EmbedderConfiguration(config_dir)
        self.env = env
        
    def create_config(
        self,
        model_name: str,
        user_id: str,
        embedder_provider: str = "openai",
        embedder_config: Optional[Dict] = None,
        enable_graph: bool = False,
        graph_config: Optional[Dict] = None,
        custom_prompt: Optional[str] = None,
    ) -> MemoryConfig:
        """Create a complete memory configuration."""
        # Get vector store config
        vector_store = self.vector_store.to_mem0_config(self.env)
        
        # Get model config
        llm = self.model.to_mem0_config(model_name)
        
        # Get embedder config
        embedder = self.embedder.to_mem0_config(
            provider=embedder_provider,
            **(embedder_config or {})
        )
        
        # Set up history database path
        base_path = os.path.expanduser("~/.anthropic_autogen/memory")
        history_db_path = os.path.join(base_path, user_id, "history.db")
        os.makedirs(os.path.dirname(history_db_path), exist_ok=True)
        
        # Create config components
        config_components = {
            "vector_store": vector_store,
            "llm": llm,
            "embedder": embedder,
            "history_db_path": history_db_path,
            "version": "v1.1",  # Always use latest version
        }
        
        # Add graph store if enabled
        if enable_graph and graph_config:
            config_components["graph_store"] = GraphStoreConfig(**graph_config)
            
        # Add custom prompt if provided
        if custom_prompt:
            config_components["custom_prompt"] = custom_prompt
            
        return MemoryConfig(**config_components)
