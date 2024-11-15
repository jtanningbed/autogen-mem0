from typing import Dict, List, Set, Optional, Any
from datetime import datetime
import asyncio
from dataclasses import dataclass

from autogen_core.base import CancellationToken
from .schema import WorkflowStep, WorkflowState
from .executor import AnthropicWorkflowExecutor
from ..core.task import TaskManager
from ..core.messaging import MessageQueue

@dataclass
class StepDependencyGraph:
    """Graph representation of step dependencies"""
    steps: Dict[str, WorkflowStep]
    dependencies: Dict[str, Set[str]]
    dependents: Dict[str, Set[str]]

class ParallelWorkflowExecutor:
    """Handles concurrent execution of workflow steps"""
    
    def __init__(
        self,
        executor: AnthropicWorkflowExecutor,
        task_manager: TaskManager,
        message_queue: MessageQueue,
        max_parallel: int = 10
    ):
        self.executor = executor
        self.task_manager = task_manager
        self.message_queue = message_queue
        self.max_parallel = max_parallel
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._semaphore = asyncio.Semaphore(max_parallel)
        
    def build_dependency_graph(self, steps: List[WorkflowStep]) -> StepDependencyGraph:
        """Build dependency graph from steps"""
        graph = StepDependencyGraph(
            steps={step.id: step for step in steps},
            dependencies={step.id: set(step.dependencies) for step in steps},
            dependents={step.id: set() for step in steps}
        )
        
        # Build reverse dependencies
        for step_id, deps in graph.dependencies.items():
            for dep_id in deps:
                graph.dependents[dep_id].add(step_id)
                
        return graph

    async def execute_parallel(
        self,
        steps: List[WorkflowStep],
        context: Dict[str, Any],
        state: WorkflowState,
        cancellation_token: Optional[CancellationToken] = None
    ) -> Dict[str, Any]:
        """Execute steps in parallel where possible"""
        graph = self.build_dependency_graph(steps)
        results: Dict[str, Any] = {}
        
        # Find initial steps (no dependencies)
        ready_steps = {
            step_id for step_id, deps in graph.dependencies.items() 
            if not deps
        }
        
        while ready_steps or self._running_tasks:
            # Start new tasks for ready steps
            for step_id in ready_steps:
                step = graph.steps[step_id]
                task = asyncio.create_task(self._execute_step_with_semaphore(
                    step,
                    context,
                    cancellation_token
                ))
                self._running_tasks[step_id] = task
                
            ready_steps.clear()
            
            # Wait for any task to complete
            if self._running_tasks:
                done, _ = await asyncio.wait(
                    self._running_tasks.values(),
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Process completed tasks
                for task in done:
                    step_id = next(
                        sid for sid, t in self._running_tasks.items() 
                        if t == task
                    )
                    del self._running_tasks[step_id]
                    
                    try:
                        result = await task
                        results[step_id] = result
                        state.completed_steps[step_id] = {
                            "completed_at": datetime.now(),
                            "result": result
                        }
                        
                        # Check for newly ready steps
                        for dependent_id in graph.dependents[step_id]:
                            if all(
                                dep_id in results 
                                for dep_id in graph.dependencies[dependent_id]
                            ):
                                ready_steps.add(dependent_id)
                                
                    except Exception as e:
                        state.failed_steps[step_id] = {
                            "failed_at": datetime.now(),
                            "error": str(e)
                        }
                        # Cancel remaining tasks
                        await self.cancel_all()
                        raise
                        
        return results

    async def _execute_step_with_semaphore(
        self,
        step: WorkflowStep,
        context: Dict[str, Any],
        cancellation_token: Optional[CancellationToken] = None
    ) -> Any:
        """Execute step with concurrency control"""
        async with self._semaphore:
            return await self.executor.execute_step(
                step,
                context,
                cancellation_token
            )

    async def cancel_all(self) -> None:
        """Cancel all running tasks"""
        for task in self._running_tasks.values():
            if not task.done():
                task.cancel()
        self._running_tasks.clear()
