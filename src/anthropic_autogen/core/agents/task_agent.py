from typing import Set, Optional, Dict
from abc import abstractmethod
from autogen_core.base import CancellationToken

from .base import BaseAgent
from ..messaging import Message, MessageCategory, TaskMessage
from ..task import TaskManager, TaskContext

class TaskAgent(BaseAgent):
    """Agent for handling tasks"""
    
    def __init__(self, *args, task_manager: TaskManager, **kwargs):
        super().__init__(*args, **kwargs)
        self._task_manager = task_manager
        self._active_tasks: Dict[str, TaskContext] = {}

    def get_subscribed_categories(self) -> Set[MessageCategory]:
        return {MessageCategory.TASK}

    async def handle_message(
        self,
        message: Message,
        cancellation_token: Optional[CancellationToken] = None
    ) -> None:
        if not isinstance(message, TaskMessage):
            return

        # Handle task message
        task_id = message.task_id
        if task_id not in self._active_tasks:
            # Create new task context
            task_context = await self._task_manager.create_task(
                task_id=task_id,
                task_type=message.task_type,
                content=message.content
            )
            self._active_tasks[task_id] = task_context

        # Process task
        await self._process_task(
            self._active_tasks[task_id],
            cancellation_token
        )

    @abstractmethod
    async def _process_task(
        self,
        task_context: TaskContext,
        cancellation_token: Optional[CancellationToken] = None
    ) -> None:
        """Process a task"""
        pass

    async def get_active_tasks(self) -> Dict[str, TaskContext]:
        """Get active tasks"""
        return self._active_tasks.copy()
