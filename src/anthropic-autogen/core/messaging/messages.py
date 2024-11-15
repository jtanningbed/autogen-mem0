from typing import Optional, Any, List, Union
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import uuid4

from autogen_core.components import Image
from autogen_core.base import AgentId
from .types import MessageCategory, MessagePriority

class BaseMessage(BaseModel):
    """Base message class for all communications"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    category: MessageCategory
    sender: Optional[AgentId] = None
    recipient: Optional[AgentId] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    priority: MessagePriority = MessagePriority.NORMAL
    metadata: dict = Field(default_factory=dict)

class ChatContent(BaseModel):
    """Content for chat messages"""
    text: str
    images: List[Image] = Field(default_factory=list)

class ChatMessage(BaseMessage):
    """Message for agent-to-agent chat communication"""
    category: MessageCategory = MessageCategory.CHAT
    content: ChatContent
    requires_response: bool = False
    timeout: Optional[float] = None

class TaskMessage(BaseMessage):
    """Message for task-related communication"""
    category: MessageCategory = MessageCategory.TASK
    task_id: str
    content: Any
    task_type: str

class ControlMessage(BaseMessage):
    """Message for system control operations"""
    category: MessageCategory = MessageCategory.CONTROL
    action: str
    parameters: dict = Field(default_factory=dict)

Message = Union[ChatMessage, TaskMessage, ControlMessage]
