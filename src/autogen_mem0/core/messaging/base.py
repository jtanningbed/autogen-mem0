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


class SystemMessage(Message):
    """System-level message."""
    content: str
    source: str = "system"

class UserMessage(Message):
    """User message."""
    content: Union[str, List[Union[str, Image]]]
    source: str = "user"


class AssistantMessage(Message):
    """Assistant message."""
    content: Union[str, List[FunctionCall]]
    source: str = "assistant"


class FunctionExecutionResult(Message):
    """Function execution result."""
    content: str
    call_id: str


class FunctionExecutionResultMessage(Message):
    """Function execution result message."""
    content: List[FunctionExecutionResult]


FinishReasons = Literal["stop", "length", "function_calls", "content_filter"]


class TopLogprob(BaseModel):
    logprob: float
    bytes: Optional[List[int]] = None


class ChatCompletionTokenLogprob(BaseModel):
    token: str
    logprob: float
    top_logprobs: Optional[List[TopLogprob] | None] = None
    bytes: Optional[List[int]] = None


class TextMessage(Message):
    """Text message."""
    content: str


class MultiModalMessage(Message):
    """Message with multiple modalities."""
    content: List[Union[str, Image]]
    

class ToolCallMessage(Message):
    """Message for tool operations."""
    tool_name: str
    tool_input: Dict[str, Any] = Field(default_factory=dict)
    tool_output: Optional[Any] = None
    source: str = "tool"


class StopMessage(Message):
    """Message requesting conversation stop."""
    content: str
    source: str = "system"


class HandoffMessage(Message):
    """Message requesting handoff to another agent."""
    content: str
    target: str
    source: str = "assistant"

class ToolCallResultMessage(Message):
    """Message containing tool execution results."""
    content: List[FunctionExecutionResult]
    source: str = "tool"
    

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
