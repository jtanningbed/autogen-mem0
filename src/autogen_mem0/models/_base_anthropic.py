"""Base implementation for Anthropic chat completion clients."""

import os
from typing import Any, AsyncGenerator, Dict, Mapping, Optional, Sequence, Union

from anthropic import AsyncAnthropic
from anthropic.types import Message
from pydantic import BaseModel

from autogen_core.base import CancellationToken
from autogen_core.components.models import (
    ChatCompletionClient,
    CreateResult,
    LLMMessage,
    ModelCapabilities,
    RequestUsage,
)
from autogen_core.components.tools import Tool, ToolSchema
from .config import AnthropicClientConfiguration


class BaseAnthropicChatCompletionClient(ChatCompletionClient):
    """Base class for Anthropic chat completion clients."""

    def __init__(
        self,
        client: AsyncAnthropic,
        create_args: Dict[str, Any],
        model_capabilities: Optional[ModelCapabilities] = None,
    ):
        """Initialize the base Anthropic chat completion client.
        
        Args:
            client: AsyncAnthropic client instance
            create_args: Arguments for message creation
            model_capabilities: Optional model capabilities override
        """
        self._client = client
        self._create_args = create_args
        self._model_capabilities = model_capabilities or self._get_default_capabilities(create_args["model"])
        
        # Usage tracking
        self._total_usage = RequestUsage(prompt_tokens=0, completion_tokens=0)
        self._actual_usage = RequestUsage(prompt_tokens=0, completion_tokens=0)

    @classmethod
    def create_from_config(cls, config: Dict[str, Any]) -> ChatCompletionClient:
        """Create a client instance from configuration."""
        raise NotImplementedError("Subclasses must implement create_from_config")

    def _get_default_capabilities(self, model: str) -> Dict[str, Any]:
        """Get default capabilities for a model."""
        # Default capabilities for Claude models
        return {
            "context_window": 100000,  # Claude has a large context window
            "supports_functions": True,  # Claude supports function calling
            "supports_json_output": True,  # Claude can output JSON
            "supports_streaming": True,  # Claude supports streaming
            "supports_vision": True,  # Claude supports vision (Claude 3)
        }

    def _convert_messages(self, messages: Sequence[LLMMessage]) -> list[Message]:
        """Convert LLMMessages to Anthropic Message format."""
        converted = []
        for msg in messages:
            if msg.role == "system":
                # Anthropic handles system messages differently
                continue
            converted.append({
                "role": "assistant" if msg.role == "assistant" else "user",
                "content": msg.content,
            })
        return converted

    async def create(
        self,
        messages: Sequence[LLMMessage],
        tools: Sequence[Tool | ToolSchema] = [],
        json_output: Optional[bool] = None,
        extra_create_args: Mapping[str, Any] = {},
        cancellation_token: Optional[CancellationToken] = None,
    ) -> CreateResult:
        """Create a chat completion."""
        raise NotImplementedError("Subclasses must implement create")

    async def create_stream(
        self,
        messages: Sequence[LLMMessage],
        tools: Sequence[Tool | ToolSchema] = [],
        json_output: Optional[bool] = None,
        extra_create_args: Mapping[str, Any] = {},
        cancellation_token: Optional[CancellationToken] = None,
    ) -> AsyncGenerator[Union[str, CreateResult], None]:
        """Create a streaming chat completion."""
        raise NotImplementedError("Subclasses must implement create_stream")

    def count_tokens(self, messages: Sequence[LLMMessage], tools: Sequence[Tool | ToolSchema] = []) -> int:
        """Count tokens in the input."""
        raise NotImplementedError("Subclasses must implement count_tokens")

    def remaining_tokens(self, messages: Sequence[LLMMessage], tools: Sequence[Tool | ToolSchema] = []) -> int:
        """Get remaining tokens for response."""
        used_tokens = self.count_tokens(messages, tools)
        return self._model_capabilities["context_window"] - used_tokens

    @property
    def capabilities(self) -> Dict[str, Any]:
        """Get model capabilities."""
        return self._model_capabilities

    def actual_usage(self) -> RequestUsage:
        """Get token usage for last request."""
        return self._actual_usage

    def total_usage(self) -> RequestUsage:
        """Get total token usage."""
        return self._total_usage
