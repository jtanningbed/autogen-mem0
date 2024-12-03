"""Configuration manager for Anthropic AutoGen."""

import os
from pathlib import Path
from typing import Dict, Any, Optional

from dotenv import load_dotenv
import yaml

from .schema import GlobalConfig, EnvironmentConfig
from mem0.configs.base import MemoryConfig

def substitute_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively substitute environment variables in configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configuration with environment variables substituted
    """
    if isinstance(config, dict):
        return {k: substitute_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [substitute_env_vars(v) for v in config]
    elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
        env_var = config[2:-1]
        return os.getenv(env_var, config)  # Return original if not found
    return config

class ConfigManager:
    """Configuration manager."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager.
        
        Args:
            config_path: Optional path to config file. If not provided, will look in default locations.
        """
        # Load environment variables
        load_dotenv()
        
        # Get base configuration directory
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = Path(__file__).parent.parent.parent.parent.parent / "config" / "config.yaml"
            
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
        # Load configuration
        with open(self.config_path) as f:
            config_dict = yaml.safe_load(f)
            
        # Substitute environment variables
        config_dict = substitute_env_vars(config_dict)
            
        # Parse configuration
        self.config = GlobalConfig(**config_dict)
        
    def get_environment_config(self, environment: Optional[str] = None) -> EnvironmentConfig:
        """Get configuration for specified environment.
        
        Args:
            environment: Environment name. If not provided, uses default environment.
            
        Returns:
            Environment configuration.
        """
        env_name = environment or self.config.default_environment
        if env_name not in self.config.environments:
            raise ValueError(f"Environment not found: {env_name}")
            
        return self.config.environments[env_name]
        
    def get_memory_config(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """Get memory configuration for specified environment.
        
        Args:
            environment: Environment name. If not provided, uses default environment.
            
        Returns:
            Raw memory configuration dictionary for mem0.
        """
        env_config = self.get_environment_config(environment)
        memory_dict = env_config.memory
        
        # Only include fields that are actually specified in our config
        config_dict = {}
        for key, value in memory_dict.items():
            if value is not None:  # Only include non-None values
                config_dict[key] = value
                
        return config_dict

    def to_mem0_config(self, environment: Optional[str] = None) -> MemoryConfig:
        """Convert memory configuration to Mem0 MemoryConfig object.
        
        Args:
            environment: Environment name. If not provided, uses default environment.
            
        Returns:
            MemoryConfig object for mem0.
        """
        config_dict = self.get_memory_config(environment)
        return MemoryConfig(**config_dict)

    def get_model_config(self, model_alias: str, environment: Optional[str] = None) -> Dict[str, Any]:
        """Get model configuration from memory.llm.config.
        
        Args:
            model_alias: Model alias/name (unused, will use config from memory.llm)
            environment: Environment name. If not provided, uses default environment.
        
        Returns:
            Model configuration dictionary from memory.llm.config
        """
        env_config = self.get_environment_config(environment)
        
        # Get model config from memory.llm.config
        if not hasattr(env_config, 'memory') or not hasattr(env_config.memory, 'llm'):
            return {}
        
        llm_config = env_config.memory.llm.config
        if not llm_config:
            return {}
        
        return {
            "model": llm_config.get("model"),
            "max_tokens": llm_config.get("max_tokens"),
            "temperature": llm_config.get("temperature"),
        }
