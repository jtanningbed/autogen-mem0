"""
Anthropic model integration for autogen-core.
Provides a ChatCompletionClient implementation for the Anthropic Claude API.
"""

from typing import List, Optional, Dict, Any
from anthropic import AsyncAnthropic
from autogen_core.components.models import (
    ChatCompletionClient,
    AssistantMessage,
    SystemMessage,
    UserMessage,
    LLMMessage
)


class AnthropicChatCompletionClient(ChatCompletionClient):
    """
    Chat completion client for Anthropic's Claude models.
    Implements the autogen-core ChatCompletionClient interface.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-opus-20240229",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ):
        """
        Initialize the Anthropic chat completion client.

        Args:
            api_key: Anthropic API key
            model: Model name to use (default: claude-3-opus-20240229)
            max_tokens: Maximum tokens to generate (default: 1024)
            temperature: Sampling temperature (default: 0.7)
            **kwargs: Additional arguments passed to AsyncAnthropic
        """
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.kwargs = kwargs

    async def create_chat_completion(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AssistantMessage:
        """
        Create a chat completion using the Anthropic API.

        Args:
            messages: List of messages in the conversation
            tools: Optional list of tools available to the model
            **kwargs: Additional arguments passed to the API

        Returns:
            AssistantMessage containing the model's response
        """
        # Convert autogen messages to Anthropic format
        anthropic_messages = []
        
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

        # Create completion request
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=anthropic_messages,
            **{**self.kwargs, **kwargs}
        )

        # Convert response to AssistantMessage
        return AssistantMessage(content=response.content[0].text)

    @property
    def model_name(self) -> str:
        """Get the name of the current model."""
        return self.model
