"""Message adaptation layer for converting between message formats."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic, Union
import json

from autogen_agentchat.messages import (
    BaseMessage as AutogenBaseMessage,
    TextMessage as AutogenTextMessage,
    ToolCallMessage as AutogenToolCallMessage, 
    ChatMessage as AutogenChatMessage
)
from autogen_core.components import FunctionCall
from autogen_core.components.models import (
    SystemMessage as CoreSystemMessage,
    UserMessage as CoreUserMessage,
    AssistantMessage as CoreAssistantMessage,
    FunctionExecutionResultMessage as CoreFunctionExecutionResultMessage,
    LLMMessage as CoreLLMMessage,
    CreateResult,
    RequestUsage
)
from anthropic.types.beta import BetaMessage as AnthropicMessage

from ..messaging.base import ChatMessage

T = TypeVar('T')
U = TypeVar('U')

class MessageAdapter(ABC, Generic[T, U]):
    """Base adapter interface for converting between message types."""

    @abstractmethod
    def adapt(self, message: T) -> U:
        """Convert from source type T to target type U."""
        pass

class AutogenMessageAdapter(MessageAdapter[ChatMessage, AutogenChatMessage]):
    """Converts our messages to autogen_agentchat messages.
    The entrypoint for our autogen_agentchat integration is AssistantAgent.on_messages_stream(), 
    which expects inputs of type `autogen_agentchat.messages.ChatMessage`
    """

    def adapt(self, messages: List[ChatMessage]) -> List[AutogenChatMessage]:
        """Convert our message to autogen message format."""
        autogen_messages: List[AutogenChatMessage] = []
        for message in messages:
            if isinstance(message.content, (str, list)):
                autogen_messages.append( AutogenTextMessage(
                    content=str(message.content),
                    source=message.source,
                    models_usage=message.models_usage,
                ))
        # raise ValueError(f"Cannot convert message with content type {type(message.content)}")
        return autogen_messages

class AnthropicRequestAdapter(MessageAdapter[List[CoreLLMMessage], List[Dict[str, Any]]]):
    """Converts autogen_core messages to Anthropic API format.
    This adapts the message types sent from autogen_agentchat (following autogen_core schemas) to Anthropic API format.
    """

    # Make roles explicit and reusable
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"
    ROLE_SYSTEM = "system"

    # Make content types explicit
    CONTENT_TYPE_TOOL_USE = "tool_use"
    CONTENT_TYPE_TOOL_RESULT = "tool_result"

    def adapt(self, messages: List[CoreLLMMessage]) -> List[Dict[str, Any]]:
        """Convert a sequence of messages to Anthropic's format.

        Args:
            message: The list of core messages to convert (typically from `autogen_core.components.models.LLMMessage`)

        Returns:
            List[Dict] with Anthropic message format:
            - For text: {"role": str, "content": str}
            - For tool calls: {"role": str, "content": List[Dict[str, Any]]}

        Raises:
            ValueError: If message type is unsupported or missing required fields
        """
        anthropic_messages = []
        
        for message in messages:
            if isinstance(message, CoreSystemMessage):
                # System messages should be handled separately by the client
                continue
                
            if isinstance(message, CoreUserMessage):
                anthropic_messages.append(self._adapt_user_message(message))
                continue
                
            if isinstance(message, CoreAssistantMessage):
                anthropic_messages.append(self._adapt_assistant_message(message))
                continue
                
            if isinstance(message, CoreFunctionExecutionResultMessage):
                anthropic_messages.append(self._adapt_function_result(message))
                continue
                
            raise ValueError(f"Unsupported message type: {type(message)}")
            
        return anthropic_messages

    def _adapt_user_message(self, message: CoreUserMessage) -> Dict[str, Any]:
        """Helper to adapt user messages."""
        return {"role": self.ROLE_USER, "content": message.content}

    def _adapt_assistant_message(self, message: CoreAssistantMessage) -> Dict[str, Any]:
        """Helper to adapt assistant messages."""
        if not isinstance(message.content, list):
            return {"role": self.ROLE_ASSISTANT, "content": message.content}

        tool_calls = []
        for call in message.content:
            if isinstance(call, FunctionCall):
                tool_calls.append({
                    "type": self.CONTENT_TYPE_TOOL_USE,
                    "id": call.id,
                    "name": call.name,
                    "input": json.loads(call.arguments),
                })

        return {"role": self.ROLE_ASSISTANT, "content": tool_calls}

    def _adapt_function_result(
        self, message: CoreFunctionExecutionResultMessage
    ) -> Dict[str, Any]:
        """Helper to adapt function results."""
        if not isinstance(message.content, list):
            message.content = [message.content]

        tool_results = []
        for result in message.content:
            call_id = getattr(result, "call_id", None)
            if call_id is None:
                raise ValueError("FunctionExecutionResult must have a call_id")

            tool_results.append({
                "type": self.CONTENT_TYPE_TOOL_RESULT,
                "tool_use_id": call_id,
                "content": str(result.content),
            })

        return {"role": self.ROLE_USER, "content": tool_results}

class AnthropicResponseAdapter(MessageAdapter[AnthropicMessage, CreateResult]):
    """Converts Anthropic API responses to autogen_core CreateResult."""

    def adapt(self, response: AnthropicMessage) -> CreateResult:
        """Convert Anthropic response to CreateResult format.
        
        Args:
            response: Raw response from Anthropic API
            
        Returns:
            CreateResult with properly formatted content and usage information
        """
        # Check if response has tool calls
        has_tool_calls = any(block.type == "tool_use" for block in response.content)

        # Keep content in native format
        if has_tool_calls:
            content = [
                FunctionCall(
                    id=block.id,
                    name=block.name,
                    arguments=json.dumps(block.input)
                )
                for block in response.content
                if block.type == "tool_use"
            ]
        else:
            content = "".join(block.text for block in response.content if block.type == "text")

        # Calculate usage
        usage = RequestUsage(
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens
        )

        return CreateResult(
            content=content,
            usage=usage,
            finish_reason=self._adapt_finish_reason(response.stop_reason, has_tool_calls),
            cached=False
        )

    def _adapt_finish_reason(self, stop_reason: str, has_tool_calls: bool) -> str:
        """Convert Anthropic stop reason to CreateResult finish reason."""
        if has_tool_calls:
            return "tool_calls"
        if stop_reason == "end_turn":
            return "stop"
        if stop_reason == "max_tokens":
            return "length"
        return stop_reason

    # old 
    def _adapt_finish_reason(self, stop_reason: Optional[str], has_tool_calls: bool = False) -> str:
        """Adapt Anthropic stop reasons to CreateResult (OpenAI) finish reasons."""
        if has_tool_calls:
            return "function_calls"
        if not stop_reason:
            return "stop"
        
        # Map Anthropic stop reasons to CreateResult finish reasons
        reason_map = {
            "end_turn": "stop",
            "stop_sequence": "stop", 
            "max_tokens": "length",
            "tool_use": "function_calls"
        }
        return reason_map.get(stop_reason, "stop")

class MessageAdapterFactory:
    """Factory for creating message adapters."""
    
    _adapters: Dict[str, MessageAdapter] = {}
    
    @classmethod
    def register(cls, source_type: str, target_type: str, adapter: MessageAdapter) -> None:
        """Register an adapter for a source -> target type conversion."""
        cls._adapters[f"{source_type}->{target_type}"] = adapter
    
    @classmethod
    def get_adapter(cls, source_type: str, target_type: str) -> Optional[MessageAdapter]:
        """Get adapter for source -> target type conversion."""
        return cls._adapters.get(f"{source_type}->{target_type}")
    
    @classmethod
    def adapt(cls, messages: Any, source_type: str, target_type: str) -> Any:
        """Convert a message from source type to target type."""
        adapter = cls.get_adapter(source_type, target_type)
        if not adapter:
            raise ValueError(f"No adapter found for conversion: {source_type} -> {target_type}")
        return adapter.adapt(messages)
