"""
Core message types for agent communication.
These define the fundamental message interfaces used throughout the system.
"""

from typing import Any, Dict, Optional, List, Type, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import uuid4

from autogen_core.base import MessageSerializer
from autogen_core.base._serialization import PydanticJsonMessageSerializer


class MessageCommon(BaseModel):
    """Common fields for all messages."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    sender: Optional[str] = None
    recipient: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def default_serializer(cls) -> List[MessageSerializer[Any]]:
        """Get default serializer for this message type."""
        return [PydanticJsonMessageSerializer(cls)]


class ChatMessage(MessageCommon):
    """Message for chat communication between agents."""
    content: str
    reply_to: Optional[str] = None


class ToolMessage(MessageCommon):
    """Message for tool execution requests and results."""
    tool_name: str
    tool_input: Dict[str, Any] = Field(default_factory=dict)
    tool_output: Optional[Any] = None


class TaskMessage(MessageCommon):
    """Message for task-related communication."""
    task_id: str = Field(default_factory=lambda: str(uuid4()))
    action: str
    status: str = Field(default="pending")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[str] = None

    def is_timed_out(self) -> bool:
        """Check if task has exceeded its timeout."""
        timeout = self.metadata.get("timeout")
        started_at = self.metadata.get("started_at")
        if not timeout or not started_at:
            return False
        return (datetime.now() - started_at).total_seconds() > timeout

    def can_retry(self) -> bool:
        """Check if task can be retried."""
        retries = self.metadata.get("retries", 0)
        max_retries = self.metadata.get("max_retries", 3)
        return retries < max_retries


class SystemMessage(MessageCommon):
    """Message for system-level notifications and events."""
    content: Any


class UserMessage(MessageCommon):
    """Message from a user to an agent."""
    content: str


class AssistantMessage(MessageCommon):
    """Message from an assistant to a user."""
    content: str


class ControlMessage(MessageCommon):
    """Message for system control and coordination."""
    command: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    content: Any = None  # Optional content for flexibility
