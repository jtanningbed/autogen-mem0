from typing import Dict, List, Set, Optional, Any
from datetime import datetime
import asyncio
from dataclasses import dataclass

from autogen_core.base import CancellationToken
from .schema import WorkflowStep, WorkflowState
from .executor import AnthropicWorkflowExecutor

@dataclass
class StepDependencyGraph:
    """Graph representation of step dependencies"""
    steps: Dict[str, WorkflowStep]
    dependencies: Dict[str, Set[str]]
    dependents: Dict[str, Set[str]]

class ParallelWorkflowExecutor:
    """Handles concurrent execution of workflow steps"""
    
    def __init__(self, executor: AnthropicWorkflowExecutor):
        self.executor = executor
        self._running_tasks: Dict[str, asyncio.Task] = {}
        
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
                task = asyncio.create_task(
                    self.executor.execute_step(
                        step,
                        context,
                        cancellation_token
                    )
                )
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

    async def cancel_all(self) -> None:
        """Cancel all running tasks"""
        for task in self._running_tasks.values():
            if not task.done():
                task.cancel()
        self._running_tasks.clear()
from typing import Optional, List
import asyncio
from autogen_core.base import CancellationToken
from ..core.task import TaskManager
from ..core.messaging import MessageQueue
from .step import WorkflowStep, StepResult
from .state import StateStore, WorkflowState

class ParallelExecutor:
    """Executes workflow steps in parallel"""
    
    def __init__(
        self,
        task_manager: TaskManager,
        message_queue: MessageQueue,
        state_store: StateStore,
        max_parallel: int = 10
    ):
        self.task_manager = task_manager
        self.message_queue = message_queue
        self.state_store = state_store
        self.max_parallel = max_parallel
        
    async def execute_workflow(
        self,
        workflow_id: str,
        steps: List[WorkflowStep],
        initial_state: Optional[dict] = None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> WorkflowState:
        """Execute workflow steps in parallel"""
        state = WorkflowState(
            workflow_id=workflow_id,
            current_step=0,
            total_steps=len(steps),
            state=initial_state or {}
        )
        
        await self.state_store.save_state(workflow_id, state)
        
        # Create tasks for parallel execution
        tasks = []
        semaphore = asyncio.Semaphore(self.max_parallel)
        
        async def execute_step(step: WorkflowStep) -> StepResult:
            async with semaphore:
                return await step.execute(
                    state=state.state,
                    task_manager=self.task_manager,
                    message_queue=self.message_queue,
                    cancellation_token=cancellation_token
                )
                
        for step in steps:
            if cancellation_token and cancellation_token.cancelled:
                break
                
            task = asyncio.create_task(execute_step(step))
            tasks.append(task)
            
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        failed = False
        for result in results:
            if isinstance(result, Exception):
                failed = True
                state.error = str(result)
                break
                
            if not result.success:
                failed = True
                state.error = result.error
                break
                
            if result.state_updates:
                state.state.update(result.state_updates)
                
        state.status = "failed" if failed else "completed"
        await self.state_store.save_state(workflow_id, state)
        
        return state
