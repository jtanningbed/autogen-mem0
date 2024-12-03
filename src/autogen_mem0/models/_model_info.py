"""Model information for Anthropic models."""

from typing import Dict

from autogen_core.components.models import ModelCapabilities

# Based on: https://docs.anthropic.com/claude/docs/models-overview
_MODEL_POINTERS = {
    # Claude 3.5 Models
    "claude-3-5-sonnet": "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-latest": "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku": "claude-3-5-haiku-20241022",
    "claude-3-5-haiku-latest": "claude-3-5-haiku-20241022",
    
    # Claude 3 Models
    "claude-3-opus": "claude-3-opus-20240229",
    "claude-3-opus-latest": "claude-3-opus-20240229",
    "claude-3-sonnet": "claude-3-sonnet-20240229",
    "claude-3-haiku": "claude-3-haiku-20240307",
    
    # AWS Bedrock Models
    "anthropic.claude-3-5-sonnet-20241022-v2:0": "claude-3-5-sonnet-20241022",
    "anthropic.claude-3-5-haiku-20241022-v1:0": "claude-3-5-haiku-20241022",
    "anthropic.claude-3-opus-20240229-v1:0": "claude-3-opus-20240229",
    "anthropic.claude-3-sonnet-20240229-v1:0": "claude-3-sonnet-20240229",
    "anthropic.claude-3-haiku-20240307-v1:0": "claude-3-haiku-20240307",
    
    # GCP Vertex AI Models
    "claude-3-5-sonnet-v2@20241022": "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku@20241022": "claude-3-5-haiku-20241022",
    "claude-3-opus@20240229": "claude-3-opus-20240229",
    "claude-3-sonnet@20240229": "claude-3-sonnet-20240229",
    "claude-3-haiku@20240307": "claude-3-haiku-20240307",
}

_MODEL_CAPABILITIES: Dict[str, ModelCapabilities] = {
    # Claude 3.5 Models
    "claude-3-5-sonnet-20241022": {
        "vision": True,
        "function_calling": True,
        "json_output": True,
        "message_batches": True,
    },
    "claude-3-5-haiku-20241022": {
        "vision": False,
        "function_calling": True,
        "json_output": True,
        "message_batches": True,
    },
    
    # Claude 3 Models
    "claude-3-opus-20240229": {
        "vision": True,
        "function_calling": True,
        "json_output": True,
        "message_batches": True,
    },
    "claude-3-sonnet-20240229": {
        "vision": True,
        "function_calling": True,
        "json_output": True,
        "message_batches": False,
    },
    "claude-3-haiku-20240307": {
        "vision": True,
        "function_calling": True,
        "json_output": True,
        "message_batches": True,
    },
}

_MODEL_TOKEN_LIMITS: Dict[str, int] = {
    # Claude 3.5 Models - 200K context, 8K output
    "claude-3-5-sonnet-20241022": 200000,
    "claude-3-5-haiku-20241022": 200000,
    
    # Claude 3 Models - 200K context, 4K output
    "claude-3-opus-20240229": 200000,
    "claude-3-sonnet-20240229": 200000,
    "claude-3-haiku-20240307": 200000,
}

_MODEL_MAX_OUTPUT_TOKENS: Dict[str, int] = {
    # Claude 3.5 Models
    "claude-3-5-sonnet-20241022": 8192,
    "claude-3-5-haiku-20241022": 8192,
    
    # Claude 3 Models
    "claude-3-opus-20240229": 4096,
    "claude-3-sonnet-20240229": 4096,
    "claude-3-haiku-20240307": 4096,
}

_MODEL_PRICING: Dict[str, Dict[str, float]] = {
    # Claude 3.5 Models
    "claude-3-5-sonnet-20241022": {
        "input_price_per_mtok": 3.00,   # $3.00 per million input tokens
        "output_price_per_mtok": 15.00,  # $15.00 per million output tokens
    },
    "claude-3-5-haiku-20241022": {
        "input_price_per_mtok": 1.00,   # $1.00 per million input tokens
        "output_price_per_mtok": 5.00,  # $5.00 per million output tokens
    },
    
    # Claude 3 Models
    "claude-3-opus-20240229": {
        "input_price_per_mtok": 15.00,  # $15.00 per million input tokens
        "output_price_per_mtok": 75.00,  # $75.00 per million output tokens
    },
    "claude-3-sonnet-20240229": {
        "input_price_per_mtok": 3.00,   # $3.00 per million input tokens
        "output_price_per_mtok": 15.00,  # $15.00 per million output tokens
    },
    "claude-3-haiku-20240307": {
        "input_price_per_mtok": 0.25,   # $0.25 per million input tokens
        "output_price_per_mtok": 1.25,  # $1.25 per million output tokens
    },
}

def resolve_model(model: str) -> str:
    """Resolve a model pointer to its actual model name."""
    return _MODEL_POINTERS.get(model, model)

def get_capabilities(model: str) -> ModelCapabilities:
    """Get the capabilities of a model."""
    model = resolve_model(model)
    return _MODEL_CAPABILITIES.get(model, {
        "vision": False,
        "function_calling": False,
        "json_output": False,
        "message_batches": False,
    })

def get_token_limit(model: str) -> int:
    """Get the token limit (context window) for a model."""
    model = resolve_model(model)
    return _MODEL_TOKEN_LIMITS.get(model, 100000)  # Default to 100k if unknown

def get_max_output_tokens(model: str) -> int:
    """Get the maximum output tokens for a model."""
    model = resolve_model(model)
    return _MODEL_MAX_OUTPUT_TOKENS.get(model, 4096)  # Default to 4k if unknown

def get_model_pricing(model: str) -> Dict[str, float]:
    """Get the pricing information for a model.
    
    Returns:
        Dict with input_price_per_mtok and output_price_per_mtok in USD.
    """
    model = resolve_model(model)
    return _MODEL_PRICING.get(model, {
        "input_price_per_mtok": 0.0,
        "output_price_per_mtok": 0.0,
    })

def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate the cost in USD for a request.
    
    Args:
        model: The model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        Total cost in USD
    """
    pricing = get_model_pricing(model)
    input_cost = (input_tokens / 1_000_000) * pricing["input_price_per_mtok"]
    output_cost = (output_tokens / 1_000_000) * pricing["output_price_per_mtok"]
    return input_cost + output_cost
