"""Registry for all adapters."""

from .messages import (
    MessageAdapter, 
    AutogenMessageAdapter,
    AnthropicRequestAdapter,
    AnthropicResponseAdapter,
    MessageAdapterFactory
)
from .tools import (
    ToolAdapter,
    AnthropicToolAdapter,
    FunctionToolAdapter,
    ToolAdapterFactory
)

def register_adapters():
    """Register all default adapters."""
    # Register message adapters
    MessageAdapterFactory.register(
        "autogen_mem0.core.messaging.ChatMessage",
        "autogen_agentchat.messages.ChatMessage",
        AutogenMessageAdapter(),
    )
    MessageAdapterFactory.register(
        "autogen_core.components.models.LLMMessage",
        "anthropic.types.beta.BetaMessage",
        AnthropicRequestAdapter(),
    )
    MessageAdapterFactory.register(
        "anthropic.types.beta.BetaMessage",
        "autogen_core.components.models.CreateResult",
        AnthropicResponseAdapter(),
    )

    # Register tool adapters
    ToolAdapterFactory.register(
        "anthropic",
        AnthropicToolAdapter()
    )
    ToolAdapterFactory.register(
        "function", 
        FunctionToolAdapter()
    )
