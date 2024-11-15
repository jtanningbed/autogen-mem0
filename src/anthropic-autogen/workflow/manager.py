from typing import Dict, List, Optional
from ..core.task import TaskManager
from ..core.messaging import MessageQueue
from ..agents.claude_agent import ClaudeAgent
from ..agents.tool_agent import ToolExecutionAgent
from ..core.tools.base import BaseTool
from autogen_core.base import CancellationToken

class WorkflowManager:
    """Manages complex workflows involving Claude and tools"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-opus-20240229",
        system_prompt: str = "",
        tools: Optional[List[BaseTool]] = None
    ):
        self.message_queue = MessageQueue()
        self.task_manager = TaskManager()
        
        # Initialize agents
        self.claude_agent = ClaudeAgent(
            agent_id="claude",
            name="Claude",
            message_queue=self.message_queue,
            api_key=api_key,
            model=model,
            system_prompt=system_prompt
        )
        
        if tools:
            self.tool_agent = ToolExecutionAgent(
                agent_id="tool_executor",
                name="Tool Executor",
                message_queue=self.message_queue,
                task_manager=self.task_manager,
                tools=tools
            )
        
    async def start(self) -> None:
        """Start all agents"""
        await self.claude_agent.start()
        if hasattr(self, 'tool_agent'):
            await self.tool_agent.start()
            
    async def stop(self) -> None:
        """Stop all agents"""
        await self.claude_agent.stop()
        if hasattr(self, 'tool_agent'):
            await self.tool_agent.stop()
            
    async def chat(
        self,
        message: str,
        cancellation_token: Optional[CancellationToken] = None
    ) -> str:
        """Send a chat message and get response"""
        response = await self.claude_agent.chat(
            message,
            cancellation_token=cancellation_token
        )
        return response.content.text if response else ""
from typing import Dict, List, Optional, Any
from autogen_core.base import CancellationToken
from autogen_core.components.workflow import (
    WorkflowContext,
    WorkflowDefinition,
    WorkflowStep
)

from ..core.messaging import MessageQueue
from ..core.task import TaskManager
from ..core.tools.base import BaseTool
from .executor import AnthropicWorkflowExecutor
from ..agents.claude_agent import ClaudeAgent

class WorkflowManager:
    """Manages workflows with Claude and tools"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-opus-20240229",
        system_prompt: str = "",
        tools: Optional[List[BaseTool]] = None
    ):
        self.message_queue = MessageQueue()
        self.task_manager = TaskManager()
        
        # Initialize workflow components
        self.executor = AnthropicWorkflowExecutor(
            message_queue=self.message_queue,
            task_manager=self.task_manager,
            tools=tools
        )
        
        self.claude_agent = ClaudeAgent(
            agent_id="claude",
            name="Claude",
            message_queue=self.message_queue,
            api_key=api_key,
            model=model,
            system_prompt=system_prompt
        )
        
    async def execute_workflow(
        self,
        workflow: WorkflowDefinition,
        context: Optional[Dict[str, Any]] = None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> Dict[str, Any]:
        """Execute a workflow"""
        workflow_context = WorkflowContext(
            owner="claude",
            workflow_id=workflow.id,
            context=context or {}
        )
        
        results = {}
        for step in workflow.steps:
            result = await self.executor.execute_step(
                step,
                workflow_context,
                cancellation_token
            )
            
            if not result.success:
                raise RuntimeError(f"Workflow step failed: {result.error}")
                
            results[step.id] = result.output
            workflow_context.context.update({
                f"step_{step.id}_output": result.output
            })
            
        return results
        
    async def start(self) -> None:
        """Start all components"""
        await self.claude_agent.start()
        
    async def stop(self) -> None:
        """Stop all components"""
        await self.claude_agent.stop()
from typing import Dict, List, Optional, Any
from datetime import datetime

from autogen_core.base import CancellationToken

from .schema import WorkflowDefinition, WorkflowState
from .executor import AnthropicWorkflowExecutor
from .parallel import ParallelWorkflowExecutor
from .persistence import WorkflowStateStore

class WorkflowManager:
    """Enhanced workflow manager with parallel execution and state persistence"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parallel_executor = ParallelWorkflowExecutor(self.executor)
        self.state_store = WorkflowStateStore()
        
    async def execute_workflow(
        self,
        workflow: WorkflowDefinition,
        context: Optional[Dict[str, Any]] = None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> Dict[str, Any]:
        """Execute a workflow with state tracking"""
        # Initialize workflow state
        state = WorkflowState(
            workflow_id=workflow.id,
            status="running",
            context=context or {}
        )
        self.state_store.save_state(state)
        
        try:
            # Execute workflow steps in parallel where possible
            results = await self.parallel_executor.execute_parallel(
                workflow.steps,
                state.context,
                state,
                cancellation_token
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
        self,
        workflow_id: str,
        cancellation_token: Optional[CancellationToken] = None
    ) -> Optional[Dict[str, Any]]:
        """Resume a failed or cancelled workflow"""
        state = self.state_store.load_state(workflow_id)
        if not state or state.status == "completed":
            return None
            
        # Get workflow definition
        workflow = self._get_workflow_definition(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
            
        # Filter out completed steps
        remaining_steps = [
            step for step in workflow.steps
            if step.id not in state.completed_steps
        ]
        
        # Resume execution
        return await self.execute_workflow(
            WorkflowDefinition(
                id=workflow_id,
                name=workflow.name,
                description=workflow.description,
                version=workflow.version,
                steps=remaining_steps
            ),
            state.context,
            cancellation_token
        )
