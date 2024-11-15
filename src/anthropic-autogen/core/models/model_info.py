from typing import Dict
from autogen_core.components.models import ModelCapabilities

# Model version mappings
MODEL_POINTERS = {
    "claude-3": "claude-3-opus-20240229",
    "claude-3-opus": "claude-3-opus-20240229",
    "claude-3-sonnet": "claude-3-sonnet-20240229",
    "claude-3-haiku": "claude-3-haiku-20240229",
}

# Capabilities for each model version
MODEL_CAPABILITIES: Dict[str, ModelCapabilities] = {
    "claude-3-opus-20240229": {
        "vision": True,
        "function_calling": True,
        "json_output": True,
    },
    "claude-3-sonnet-20240229": {
        "vision": True,
        "function_calling": True,
        "json_output": True,
    },
    "claude-3-haiku-20240229": {
        "vision": True,
        "function_calling": True,
        "json_output": True,
    },
}

# Token limits for each model
MODEL_TOKEN_LIMITS: Dict[str, int] = {
    "claude-3-opus-20240229": 200000,
    "claude-3-sonnet-20240229": 200000,
    "claude-3-haiku-20240229": 200000,
}

def resolve_model(model: str) -> str:
    """Resolve model alias to actual model version"""
    if model in MODEL_POINTERS:
        return MODEL_POINTERS[model]
    return model

def get_capabilities(model: str) -> ModelCapabilities:
    """Get capabilities for a specific model"""
    resolved_model = resolve_model(model)
    return MODEL_CAPABILITIES[resolved_model]

def get_token_limit(model: str) -> int:
    """Get token limit for a specific model"""
    resolved_model = resolve_model(model)
    return MODEL_TOKEN_LIMITS[resolved_model]
