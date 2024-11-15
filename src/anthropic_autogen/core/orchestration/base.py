from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union
from autogen_core.base import AgentId, CancellationToken
from ..messaging import Message, MessageQueue
from ..task import TaskManager
from ..agents import BaseAgent, AgentFactory
from ..tools.base import BaseTool
from .types import OrchestrationRequest, OrchestrationResult

class BaseOrchestrator(ABC):
    """Base interface for all orchestrators"""
    
    def __init__(
        self,
        message_queue: MessageQueue,
        task_manager: TaskManager,
        agent_factory: Optional[AgentFactory] = None
    ):
        self.message_queue = message_queue
        self.task_manager = task_manager
        self.agent_factory = agent_factory or AgentFactory()
        
    @abstractmethod
    async def register_component(self, component: Union[BaseAgent, BaseTool]) -> None:
        """Register a component (agent or tool)"""
        pass
        
    @abstractmethod
    async def unregister_component(self, component_id: str) -> None:
        """Unregister a component"""
        pass
        
    @abstractmethod
    async def execute(
        self,
        request: OrchestrationRequest,
        cancellation_token: Optional[CancellationToken] = None
    ) -> OrchestrationResult:
        """Execute an orchestration request"""
        pass
