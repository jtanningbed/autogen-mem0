"""Anthropic chat completion client."""

from typing import Any, Dict, List, Optional, AsyncGenerator
import os
import json
from anthropic import AsyncAnthropic

from autogen_core.base import CancellationToken
from autogen_core.components import FunctionCall
from autogen_core.components.models import (
    SystemMessage,
    LLMMessage,
    CreateResult,
    RequestUsage,
)
from autogen_core.components.tools import Tool

from ..core.adapters import MessageAdapterFactory, ToolAdapterFactory
from ..core.errors import AnthropicError
from ._base_anthropic import BaseAnthropicChatCompletionClient
from ._model_info import (
    calculate_cost
)

import logging
logger = logging.getLogger(__name__)

class AnthropicChatCompletionClient(BaseAnthropicChatCompletionClient):
    """Chat completion client for Anthropic's Claude models."""

    def __init__(self, **kwargs: Any):
        logger.debug("[AnthropicClient:__init__] Initializing client")
        logger.debug("[AnthropicClient:__init__] Input kwargs: %s", kwargs)

        if "model" not in kwargs:
            raise ValueError("model is required for AnthropicChatCompletionClient")

        # Get API key
        api_key = kwargs.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("No API key provided")

        self._prompt_caching = True if kwargs.get("prompt_caching") else False

        # Initialize client
        self._client = AsyncAnthropic(api_key=api_key)

        # Get model configuration
        config_manager = kwargs.get("config_manager")
        if config_manager:
            model_config = config_manager.get_model_config(kwargs["model"])
            # Update kwargs with model config, but don't override explicit settings
            for key, value in model_config.items():
                if key not in kwargs:
                    kwargs[key] = value

        # Store model name
        self._model = kwargs.get("model", "claude-3-5-sonnet-20241022")

        # Store create args
        self._max_tokens = kwargs.get("max_tokens", 1024)

        # Initialize cost tracking
        self._last_request_cost = 0.0
        self._total_cost = 0.0

        logger.info("[AnthropicClient:__init__] Client initialization complete")

    async def create(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Tool]] = None,
        cancellation_token: Optional[CancellationToken] = None,
    ) -> CreateResult:
        """Create a chat completion."""
        try:
            # Prepared request
            create_args = {
                "model": self._model,
                "max_tokens": self._max_tokens,
            }

            # Extract system message and convert other messages
            system_message = None
            for message in messages:
                if isinstance(message, SystemMessage):
                    if system_message is None:
                        create_args["system"] = message.content
                    else:
                        raise ValueError("Multiple system messages not supported")

            # Convert messages
            anthropic_messages = MessageAdapterFactory.adapt(
                messages, 
                "autogen_core.components.models.LLMMessage", 
                "anthropic.types.beta.BetaMessage"
            )

            create_args["messages"] = anthropic_messages
            logger.info(f"{anthropic_messages=}")

            # Convert tools
            if tools:
                try: 
                    anthropic_tools = ToolAdapterFactory.adapt_tools(tools, "anthropic")
                    create_args["tools"] = anthropic_tools
                    create_args["tool_choice"] = {"type": "auto"}
                except Exception as e:
                    logger.error("[AnthropicClient:create] Error converting tools: %s", str(e))
                    raise AnthropicError(f"Failed to convert tools: {str(e)}") from e

            all_args = {
                **create_args
            }

            logger.debug("[AnthropicClient:create] Raw request parameters: %s", json.dumps(all_args, indent=2))

            # Make API call
            if self._prompt_caching:
                logger.debug("[AnthropicClient:create] Prompt caching enabled, using prompt_caching completion")
                future = self._client.beta.prompt_caching.messages.create(**all_args)
            else:
                future = self._client.beta.messages.create(**all_args)

            if cancellation_token:
                cancellation_token.link_future(future)

            response = await future

            # Convert response
            result = MessageAdapterFactory.adapt(
                response,
                "anthropic.types.beta.BetaMessage",
                "autogen_core.components.models.CreateResult"
            )

            # Update client state
            self._last_request_cost = calculate_cost(
                self._model,
                result.usage.prompt_tokens,
                result.usage.completion_tokens
            )
            self._total_cost += self._last_request_cost

            logger.debug("[AnthropicClient:create] Returning createResult: %s", result)
            return result

        except Exception as e:
            logger.error("[AnthropicClient:create] Error during API call: %s", str(e))
            raise AnthropicError(str(e)) from e

    async def create_stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Tool]] = None,
        cancellation_token: Optional[CancellationToken] = None,
    ) -> AsyncGenerator[CreateResult, None]:
        """Create a streaming chat completion."""
        try:
            # Prepare base request
            create_args = {
                "model": self._model,
                "max_tokens": self._max_tokens,
                "stream": True,
            }

            # Extract system message and convert other messages
            system_message = None
            for message in messages:
                if isinstance(message, SystemMessage):
                    if system_message is None:
                        create_args["system"] = message.content
                    else:
                        raise ValueError("Multiple system messages not supported")

            # Convert messages
            anthropic_messages = MessageAdapterFactory.adapt(
                messages,
                "autogen_core.components.models.LLMMessage",
                "anthropic.types.beta.BetaMessage"
            )
            create_args["messages"] = anthropic_messages

            # Convert tools
            if tools:
                try:
                    anthropic_tools = ToolAdapterFactory.adapt_tools(tools, "anthropic")
                    create_args["tools"] = anthropic_tools
                    create_args["tool_choice"] = {"type": "auto"}
                except Exception as e:
                    logger.error("[AnthropicClient:create_stream] Error converting tools: %s", str(e))
                    raise AnthropicError(f"Failed to convert tools: {str(e)}") from e

            logger.debug("[AnthropicClient:create_stream] Raw request parameters: %s", 
                        json.dumps(create_args, indent=2))

            # Make streaming API call
            if self._prompt_caching:
                stream = self._client.beta.prompt_caching.messages.create(**create_args)
            else:
                stream = self._client.beta.messages.create(**create_args)

            if cancellation_token:
                cancellation_token.link_future(stream)

            logger.debug("[AnthropicClient:create_stream] Got stream response")
            message_data = None
            current_text = []
            current_tool_calls = []

            async for event in stream:
                if event.type == "message_start":
                    message_data = event
                elif event.type == "content_block_start":
                    if event.content_block.type == "tool_use":
                        # Accumulate tool calls
                        current_tool_calls.append(FunctionCall(
                            id=event.content_block.id,
                            name=event.content_block.name,
                            arguments=json.dumps(event.content_block.input)
                        ))
                elif event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        # Accumulate text
                        current_text.append(event.delta.text)
                elif event.type == "message_delta":
                    # Message complete
                    if message_data and message_data.usage:
                        # Final message with usage stats
                        usage = RequestUsage(
                            prompt_tokens=message_data.usage.input_tokens,
                            completion_tokens=message_data.usage.output_tokens
                        )

                        # Return tool calls or text, not both
                        if current_tool_calls:
                            yield CreateResult(
                                content=current_tool_calls,
                                usage=usage,
                                finish_reason="tool_calls",
                                cached=False
                            )
                        else:
                            yield CreateResult(
                                content="".join(current_text),
                                usage=usage,
                                finish_reason="stop",
                                cached=False
                            )

                        # Reset accumulators
                        current_text = []
                        current_tool_calls = []
                        message_data = None

        except Exception as e:
            logger.error("[AnthropicClient:create_stream] Error during streaming: %s", str(e))
            raise AnthropicError(str(e)) from e

    @classmethod
    def create_from_config(cls, config: Dict[str, Any]) -> "AnthropicChatCompletionClient":
        """Create a client instance from configuration."""
        logger.debug("[AnthropicClient:create_from_config] Creating client from config: %s", config)
        return cls(**config)

    @property
    def last_request_cost(self) -> float:
        """Get the cost of the last request in USD."""
        return self._last_request_cost

    @property
    def total_cost(self) -> float:
        """Get the total cost of all requests in USD."""
        return self._total_cost
