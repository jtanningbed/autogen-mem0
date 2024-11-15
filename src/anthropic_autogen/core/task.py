from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4
import asyncio

from autogen_core.base import AgentId, CancellationToken
from enum import Enum

class TaskState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass
class TaskContext:
    """Context for tracking task execution"""
    owner: AgentId
    task_id: str = field(default_factory=lambda: str(uuid4()))
    state: TaskState = TaskState.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    cancellation_token: CancellationToken = field(default_factory=CancellationToken)
    retries: int = 0
    max_retries: int = 3
    retry_delay: float = 1.0
    last_error: Optional[str] = None

    def is_timed_out(self) -> bool:
        if not self.timeout or not self.started_at:
            return False
        return (datetime.now() - self.started_at).total_seconds() > self.timeout

class TaskManager:
    """Manages task lifecycle and dependencies"""
    
    def __init__(self):
        self._tasks: Dict[str, TaskContext] = {}
        self._state_callbacks: Dict[TaskState, List[callable]] = {}
        
    async def create_task(
        self,
        owner: AgentId,
        timeout: Optional[float] = None,
        dependencies: Optional[List[str]] = None
    ) -> TaskContext:
        """Create a new task"""
        task = TaskContext(
            owner=owner,
            timeout=timeout,
            dependencies=dependencies or []
        )
        self._tasks[task.task_id] = task
        return task

    async def start_task(self, task_id: str) -> None:
        """Start task execution"""
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
            
        if task.state != TaskState.PENDING:
            raise ValueError(f"Task {task_id} is not in PENDING state")
            
        # Check dependencies
        for dep_id in task.dependencies:
            dep = self._tasks.get(dep_id)
            if not dep or dep.state != TaskState.COMPLETED:
                raise ValueError(f"Dependency {dep_id} not satisfied")
                
        task.state = TaskState.RUNNING
        task.started_at = datetime.now()
        await self._notify_state_change(task)

    async def complete_task(self, task_id: str, results: Optional[Dict[str, Any]] = None) -> None:
        """Mark task as completed"""
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
            
        task.state = TaskState.COMPLETED
        task.completed_at = datetime.now()
        if results:
            task.results.update(results)
        await self._notify_state_change(task)

    async def fail_task(self, task_id: str, error: Optional[str] = None) -> None:
        """Mark task as failed"""
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
            
        task.state = TaskState.FAILED
        task.completed_at = datetime.now()
        if error:
            task.results["error"] = error
        await self._notify_state_change(task)

    async def cancel_task(self, task_id: str) -> None:
        """Cancel task execution"""
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
            
        task.state = TaskState.CANCELLED
        task.completed_at = datetime.now()
        task.cancellation_token.cancel()
        await self._notify_state_change(task)
        
        # Cancel dependent tasks
        await self.cancel_dependent_tasks(task_id)

    async def retry_task(self, task_id: str) -> None:
        """Retry a failed task"""
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
            
        if task.retries >= task.max_retries:
            raise ValueError(f"Task {task_id} exceeded retry limit")
            
        task.retries += 1
        task.state = TaskState.PENDING
        task.started_at = None
        task.completed_at = None
        
        await asyncio.sleep(task.retry_delay)
        await self.start_task(task_id)

    async def get_dependent_tasks(self, task_id: str) -> list[str]:
        """Get tasks that depend on given task"""
        dependent_tasks = []
        for task in self._tasks.values():
            if task_id in task.dependencies:
                dependent_tasks.append(task.task_id)
        return dependent_tasks

    async def cancel_dependent_tasks(self, task_id: str) -> None:
        """Cancel all tasks that depend on the given task"""
        dependent_tasks = await self.get_dependent_tasks(task_id)
        for dep_id in dependent_tasks:
            await self.cancel_task(dep_id)

    def register_state_callback(
        self,
        state: TaskState,
        callback: callable
    ) -> None:
        """Register callback for task state changes"""
        if state not in self._state_callbacks:
            self._state_callbacks[state] = []
        self._state_callbacks[state].append(callback)

    async def _notify_state_change(self, task: TaskContext) -> None:
        """Notify callbacks of task state changes"""
        callbacks = self._state_callbacks.get(task.state, [])
        for callback in callbacks:
            try:
                await callback(task)
            except Exception as e:
                # Log error but continue with other callbacks
                print(f"Error in state change callback: {e}")

    def get_task(self, task_id: str) -> Optional[TaskContext]:
        """Get task by ID"""
        return self._tasks.get(task_id)

    def get_tasks_by_owner(self, owner: AgentId) -> List[TaskContext]:
        """Get all tasks owned by an agent"""
        return [task for task in self._tasks.values() if task.owner == owner]

    def get_active_tasks(self) -> List[TaskContext]:
        """Get all tasks that are not in a terminal state"""
        return [
            task for task in self._tasks.values()
            if task.state in [TaskState.PENDING, TaskState.RUNNING]
        ]
