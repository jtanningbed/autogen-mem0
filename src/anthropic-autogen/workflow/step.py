from typing import Optional, Dict
from pydantic import BaseModel
from enum import Enum
from autogen_core.base import CancellationToken
from ..core.task import TaskManager
from ..core.messaging import MessageQueue

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class StepResult(BaseModel):
    """Result of a workflow step execution"""
    success: bool
    error: Optional[str] = None
    state_updates: Optional[Dict] = None

class WorkflowStep:
    """Base class for workflow steps"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.status = StepStatus.PENDING
        
    async def execute(
        self,
        state: Dict,
        task_manager: TaskManager,
        message_queue: MessageQueue,
        cancellation_token: Optional[CancellationToken] = None
    ) -> StepResult:
        """Execute the workflow step"""
        self.status = StepStatus.RUNNING
        
        try:
            result = await self._execute_impl(
                state,
                task_manager,
                message_queue,
                cancellation_token
            )
            self.status = StepStatus.COMPLETED
            return result
            
        except Exception as e:
            self.status = StepStatus.FAILED
            return StepResult(
                success=False,
                error=str(e)
            )
            
    async def _execute_impl(
        self,
        state: Dict,
        task_manager: TaskManager,
        message_queue: MessageQueue,
        cancellation_token: Optional[CancellationToken] = None
    ) -> StepResult:
        """Implementation of step execution logic"""
        raise NotImplementedError()
