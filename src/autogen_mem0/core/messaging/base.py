"""
Core message types for agent communication.
These define the fundamental message interfaces used throughout the system.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Literal
from typing_extensions import get_args

from pydantic import BaseModel, ConfigDict, Field
from autogen_core.components import Image, FunctionCall
from autogen_core.components.models import (
    FunctionExecutionResult as CoreFunctionExecutionResult,
    FunctionExecutionResultMessage as CoreFunctionExecutionResultMessage,
    RequestUsage, 
    SystemMessage as CoreSystemMessage,
    UserMessage as CoreUserMessage,
    AssistantMessage as CoreAssistantMessage,
    TopLogprob as CoreTopLogprob,
    ChatCompletionTokenLogprob as CoreChatCompletionTokenLogprob,
    CreateResult
)
from autogen_agentchat.messages import (
    AgentMessage as AutogenMessage,
    TextMessage as AutogenTextMessage,
    MultiModalMessage as AutogenMultiModalMessage,
    ToolCallMessage as AutogenToolCallMessage,
    ToolCallResultMessage as AutogenToolCallResultMessage,
    StopMessage as AutogenStopMessage,
    HandoffMessage as AutogenHandoffMessage
)


class Message(BaseModel):
    """Base message class."""
    source: str
    models_usage: Optional[RequestUsage] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_autogen_message(self) -> AutogenMessage:
        """Convert to autogen message type."""
        if isinstance(self.content, (str, list)):
            return AutogenTextMessage(
                content=str(self.content),
                source=self.source,
                models_usage=self.models_usage
            )
        raise ValueError(f"Cannot convert message with content type {type(self.content)}")


class SystemMessage(Message):
    """System-level message."""
    content: str
    source: str = "system"

    def to_core_message(self) -> CoreSystemMessage:
        return CoreSystemMessage(content=self.content)

    def to_autogen_message(self) -> AutogenTextMessage:
        return AutogenTextMessage(
            content=self.content,
            source=self.source,
            models_usage=self.models_usage
        )


class UserMessage(Message):
    """User message."""
    content: Union[str, List[Union[str, Image]]]
    source: str = "user"

    def to_core_message(self) -> CoreUserMessage:
        return CoreUserMessage(content=self.content, source=self.source)


class AssistantMessage(Message):
    """Assistant message."""
    content: Union[str, List[FunctionCall]]
    source: str = "assistant"

    def to_core_message(self) -> CoreAssistantMessage:
        return CoreAssistantMessage(content=self.content, source=self.source)


class FunctionExecutionResult(Message):
    """Function execution result."""
    content: str
    call_id: str

    def to_core_message(self) -> CoreFunctionExecutionResult:
        return CoreFunctionExecutionResult(content=self.content, call_id=self.call_id)


class FunctionExecutionResultMessage(Message):
    """Function execution result message."""
    content: List[FunctionExecutionResult]

    def to_core_message(self) -> CoreFunctionExecutionResultMessage:
        return CoreFunctionExecutionResultMessage(content=self.content)


FinishReasons = Literal["stop", "length", "function_calls", "content_filter"]


class TopLogprob(BaseModel):
    logprob: float
    bytes: Optional[List[int]] = None

    def to_core_message(self) -> CoreTopLogprob:
        return CoreTopLogprob(logprob=self.logprob, bytes=self.bytes)


class ChatCompletionTokenLogprob(BaseModel):
    token: str
    logprob: float
    top_logprobs: Optional[List[TopLogprob] | None] = None
    bytes: Optional[List[int]] = None

    def to_core_message(self) -> CoreChatCompletionTokenLogprob:
        return CoreChatCompletionTokenLogprob(token=self.token, logprob=self.logprob, top_logprobs=self.top_logprobs, bytes=self.bytes)


class TextMessage(Message):
    """Text message."""
    content: str

    def to_autogen_message(self) -> AutogenTextMessage:
        return AutogenTextMessage(
            content=self.content,
            models_usage=self.models_usage
        )

class MultiModalMessage(Message):
    """Message with multiple modalities."""
    content: List[Union[str, Image]]
    
    def to_autogen_message(self) -> AutogenMultiModalMessage:
        return AutogenMultiModalMessage(
            content=self.content,
            models_usage=self.models_usage
        )

class ToolCallMessage(Message):
    """Message for tool operations."""
    tool_name: str
    tool_input: Dict[str, Any] = Field(default_factory=dict)
    tool_output: Optional[Any] = None
    source: str = "tool"
    
    def to_autogen_message(self) -> AutogenToolCallMessage:
        return AutogenToolCallMessage(
            content=[FunctionCall(name=self.tool_name, arguments=self.tool_input)],
            source=self.source,
            models_usage=self.models_usage
        )

class StopMessage(Message):
    """Message requesting conversation stop."""
    content: str
    source: str = "system"
    
    def to_autogen_message(self) -> AutogenStopMessage:
        return AutogenStopMessage(
            content=self.content,
            source=self.source,
            models_usage=self.models_usage
        )

class HandoffMessage(Message):
    """Message requesting handoff to another agent."""
    content: str
    target: str
    source: str = "assistant"
    
    def to_autogen_message(self) -> AutogenHandoffMessage:
        return AutogenHandoffMessage(
            content=self.content,
            target=self.target,
            source=self.source,
            models_usage=self.models_usage
        )

class ToolCallResultMessage(Message):
    """Message containing tool execution results."""
    content: List[FunctionExecutionResult]
    source: str = "tool"
    
    def to_autogen_message(self) -> AutogenToolCallResultMessage:
        return AutogenToolCallResultMessage(
            content=self.content,
            source=self.source,
            models_usage=self.models_usage
        )

# Type for all messages
LLMMessage = SystemMessage | UserMessage | AssistantMessage | FunctionExecutionResultMessage
"""LLM specific messages for interfacing with a ChatCompletionClient."""

InnerMessage = ToolCallMessage | ToolCallResultMessage
"""Messages for intra-agent monologues."""

ChatMessage = TextMessage | MultiModalMessage | StopMessage | HandoffMessage
"""Messages for agent-to-agent communication."""

AgentMessage = (
    TextMessage
    | MultiModalMessage
    | StopMessage
    | HandoffMessage
    | ToolCallMessage
    | ToolCallResultMessage
)
"""All agentmessage types."""

class MessageRegistry:
    """Registry of available message types."""
    _types: Dict[str, type] = {}
    
    @classmethod
    def register(cls, message_type: type):
        """Register a message type."""
        cls._types[message_type.__name__] = message_type
    
    @classmethod
    def get(cls, name: str) -> type:
        """Get a message type by name."""
        return cls._types[name]

# Register all message types from LLMMessage
for msg_type in get_args(LLMMessage):
    MessageRegistry.register(msg_type)
