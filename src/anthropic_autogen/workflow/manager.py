from typing import Dict, List, Optional, Any, Protocol
from datetime import datetime

from autogen_core.base import CancellationToken
from .schema import WorkflowDefinition, WorkflowState
from .executor import WorkflowExecutor
from .parallel import ParallelWorkflowExecutor
from .persistence import WorkflowStateStore
from ..core import BaseAgent

class WorkflowManager:
    """Generic workflow manager supporting multiple agents and tools."""

    def __init__(
        self,
        executor: WorkflowExecutor,
        parallel_executor: Optional[ParallelWorkflowExecutor] = None,
        state_store: Optional[WorkflowStateStore] = None,
        agents: Optional[List[BaseAgent]] = None,
    ):
        self.executor = executor
        self.parallel_executor = parallel_executor or ParallelWorkflowExecutor(executor)
        self.state_store = state_store or WorkflowStateStore()
        self.agents = agents or []

    async def start_agents(self) -> None:
        """Start all agents."""
        for agent in self.agents:
            await agent.start()

    async def stop_agents(self) -> None:
        """Stop all agents."""
        for agent in self.agents:
            await agent.stop()

    async def execute_workflow(
        self,
        workflow: WorkflowDefinition,
        context: Optional[Dict[str, Any]] = None,
        parallel: bool = False,
        cancellation_token: Optional[CancellationToken] = None,
    ) -> Dict[str, Any]:
        """Execute a workflow with state tracking."""
        state = WorkflowState(
            workflow_id=workflow.id, status="running", context=context or {}
        )
        self.state_store.save_state(state)

        try:
            executor = self.parallel_executor if parallel else self.executor
            results = await executor.execute_workflow(
                workflow.steps,
                context=state.context,
                cancellation_token=cancellation_token,
            )

            state.status = "completed"
            state.end_time = datetime.now()
            self.state_store.save_state(state)

            return results

        except Exception as e:
            state.status = "failed"
            state.end_time = datetime.now()
            state.context["error"] = str(e)
            self.state_store.save_state(state)
            raise

    async def resume_workflow(
        self, workflow_id: str, cancellation_token: Optional[CancellationToken] = None
    ) -> Optional[Dict[str, Any]]:
        """Resume a failed or cancelled workflow."""
        state = self.state_store.load_state(workflow_id)
        if not state or state.status == "completed":
            return None

        workflow = self._get_workflow_definition(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        remaining_steps = [
            step for step in workflow.steps if step.id not in state.completed_steps
        ]

        return await self.execute_workflow(
            WorkflowDefinition(
                id=workflow_id,
                name=workflow.name,
                description=workflow.description,
                version=workflow.version,
                steps=remaining_steps,
            ),
            state.context,
            cancellation_token,
        )

    def _get_workflow_definition(
        self, workflow_id: str
    ) -> Optional[WorkflowDefinition]:
        """Retrieve a workflow definition (placeholder for actual logic)."""
        return None
