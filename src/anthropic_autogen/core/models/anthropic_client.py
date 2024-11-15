import asyncio
from typing import Any, AsyncGenerator, Dict, List, Mapping, Optional, Sequence, Union, cast

import anthropic
from anthropic.types import Message as AnthropicMessage
from autogen_core.base import CancellationToken
from autogen_core.components.models import (
    ChatCompletionClient,
    CreateResult,
    LLMMessage,
    ModelCapabilities,
    RequestUsage,
    SystemMessage,
    UserMessage,
    AssistantMessage,
)
from autogen_core.components.tools import Tool, ToolSchema
from pydantic import BaseModel
from typing_extensions import TypedDict

class AnthropicClientConfig(TypedDict, total=False):
    """Configuration for AnthropicChatCompletionClient"""
    model: str  # e.g. "claude-3-opus-20240229"
    api_key: str
    max_tokens: Optional[int]
    temperature: Optional[float]
    top_p: Optional[float]
    timeout: Optional[float]

class AnthropicChatCompletionClient(ChatCompletionClient):
    """Chat completion client for Anthropic's Claude models"""

    def __init__(self, **kwargs: AnthropicClientConfig) -> None:
        if "model" not in kwargs:
            raise ValueError("model is required")
        if "api_key" not in kwargs:
            raise ValueError("api_key is required")

        self._client = anthropic.AsyncAnthropic(api_key=kwargs["api_key"])
        self._model = kwargs["model"]
        self._config = kwargs
        self._total_usage = RequestUsage(prompt_tokens=0, completion_tokens=0)
        self._actual_usage = RequestUsage(prompt_tokens=0, completion_tokens=0)

    def _convert_messages(self, messages: Sequence[LLMMessage]) -> List[AnthropicMessage]:
        """Convert autogen messages to Anthropic message format"""
        anthropic_messages: List[AnthropicMessage] = []
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                anthropic_messages.append({
                    "role": "system",
                    "content": msg.content
                })
            elif isinstance(msg, UserMessage):
                anthropic_messages.append({
                    "role": "user", 
                    "content": msg.content
                })
            elif isinstance(msg, AssistantMessage):
                anthropic_messages.append({
                    "role": "assistant",
                    "content": msg.content
                })
                
        return anthropic_messages

    async def create(
        self,
        messages: Sequence[LLMMessage],
        tools: Sequence[Tool | ToolSchema] = [],
        json_output: Optional[bool] = None,
        extra_create_args: Mapping[str, Any] = {},
        cancellation_token: Optional[CancellationToken] = None,
    ) -> CreateResult:
        """Create a chat completion using Anthropic's API"""
        
        anthropic_messages = self._convert_messages(messages)
        
        # Prepare the completion request
        request_args = {
            "model": self._model,
            "messages": anthropic_messages,
            "max_tokens": self._config.get("max_tokens"),
            "temperature": self._config.get("temperature"),
            "top_p": self._config.get("top_p"),
        }
        request_args.update(extra_create_args)

        # Create a task for the completion
        completion_task = asyncio.create_task(
            self._client.messages.create(**request_args)
        )

        if cancellation_token:
            cancellation_token.link_future(completion_task)

        try:
            response = await completion_task
        except Exception as e:
            if isinstance(e, asyncio.CancelledError):
                raise
            raise RuntimeError(f"Error from Anthropic API: {str(e)}") from e

        # Update usage statistics
        usage = RequestUsage(
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens
        )
        self._actual_usage = usage
        self._total_usage = RequestUsage(
            prompt_tokens=self._total_usage.prompt_tokens + usage.prompt_tokens,
            completion_tokens=self._total_usage.completion_tokens + usage.completion_tokens
        )

        return CreateResult(
            content=response.content[0].text,
            finish_reason=response.stop_reason or "stop",
            usage=usage,
            cached=False
        )

    async def create_stream(
        self,
        messages: Sequence[LLMMessage],
        tools: Sequence[Tool | ToolSchema] = [],
        json_output: Optional[bool] = None,
        extra_create_args: Mapping[str, Any] = {},
        cancellation_token: Optional[CancellationToken] = None,
    ) -> AsyncGenerator[Union[str, CreateResult], None]:
        """Create a streaming chat completion"""
        
        anthropic_messages = self._convert_messages(messages)
        
        request_args = {
            "model": self._model,
            "messages": anthropic_messages,
            "max_tokens": self._config.get("max_tokens"),
            "temperature": self._config.get("temperature"),
            "top_p": self._config.get("top_p"),
            "stream": True
        }
        request_args.update(extra_create_args)

        stream_task = asyncio.create_task(
            self._client.messages.create(**request_args)
        )

        if cancellation_token:
            cancellation_token.link_future(stream_task)

        try:
            async for chunk in await stream_task:
                if chunk.type == "message_delta":
                    if chunk.delta.text:
                        yield chunk.delta.text
                elif chunk.type == "message_stop":
                    # Final message with usage stats
                    usage = RequestUsage(
                        prompt_tokens=chunk.usage.input_tokens,
                        completion_tokens=chunk.usage.output_tokens
                    )
                    self._actual_usage = usage
                    self._total_usage = RequestUsage(
                        prompt_tokens=self._total_usage.prompt_tokens + usage.prompt_tokens,
                        completion_tokens=self._total_usage.completion_tokens + usage.completion_tokens
                    )
                    yield CreateResult(
                        content="",
                        finish_reason=chunk.stop_reason or "stop",
                        usage=usage,
                        cached=False
                    )
        except Exception as e:
            if isinstance(e, asyncio.CancelledError):
                raise
            raise RuntimeError(f"Error from Anthropic API: {str(e)}") from e

    def actual_usage(self) -> RequestUsage:
        return self._actual_usage

    def total_usage(self) -> RequestUsage:
        return self._total_usage

    @property
    def capabilities(self) -> ModelCapabilities:
        """Define capabilities for Claude models"""
        return {
            "vision": True,  # Claude 3 supports vision
            "function_calling": True,  # Through system prompts
            "json_output": True,  # Through system prompts
        }

    def count_tokens(self, messages: Sequence[LLMMessage], tools: Sequence[Tool | ToolSchema] = []) -> int:
        """Count tokens for the messages"""
        anthropic_messages = self._convert_messages(messages)
        return self._client.count_tokens(anthropic_messages)

    def remaining_tokens(self, messages: Sequence[LLMMessage], tools: Sequence[Tool | ToolSchema] = []) -> int:
        """Calculate remaining tokens based on model's context window"""
        # Claude 3 models have different context windows:
        context_windows = {
            "claude-3-opus": 200000,
            "claude-3-sonnet": 200000,
            "claude-3-haiku": 200000,
        }
        
        # Get base model name without version
        base_model = "-".join(self._model.split("-")[:-1])
        context_window = context_windows.get(base_model, 100000)
        
        used_tokens = self.count_tokens(messages, tools)
        return context_window - used_tokens
