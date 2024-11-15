from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from autogen_core.base import AgentId, CancellationToken
from ..messaging import Message, MessageQueue
from ..task import TaskManager

class BaseOrchestrator(ABC):
    """Base interface for all orchestrators"""
    
    def __init__(
        self,
        message_queue: MessageQueue,
        task_manager: TaskManager
    ):
        self.message_queue = message_queue
        self.task_manager = task_manager
        
    @abstractmethod
    async def start(self) -> None:
        """Start the orchestrator"""
        pass
        
    @abstractmethod
    async def stop(self) -> None:
        """Stop the orchestrator"""
        pass
        
    @abstractmethod
    async def send_message(
        self,
        message: Message,
        cancellation_token: Optional[CancellationToken] = None
    ) -> None:
        """Send a message through the orchestrator"""
        pass
